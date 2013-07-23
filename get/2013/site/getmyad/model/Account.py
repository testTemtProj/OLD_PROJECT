# This Python file uses the following encoding: utf-8
from getmyad.model import mq
from uuid import uuid1
from getmyad.model.Informer import Informer
from getmyad.model.StatisticReports import StatisticReport
from pylons import app_globals
import datetime
import getmyad.lib.helpers as h
import pymongo
import logging

log = logging.getLogger(__name__)


class Account(object):
    """ Аккаунт пользователя """
    
    class AlreadyExistsError(Exception):
        ''' Попытка добавить существующий логин '''
        def __init__(self, login):
            self.login = login
        def __str__(self):
            return 'Account with login %s is already used' % self.login
        
    class NotFoundError(Exception):
        ''' Указанный аккаунт не найден '''
        def __init__(self, login):
            self.login = login
        def __str__(self):
            return 'Account %s not found' % self.login
        
    class UpdateError(Exception):
        ''' Ошибка обновления аккаунта'''
        def __init__(self, login):
            self.login = login
        def __str__(self):
            return 'Account %s was not updated' % self.login
    
    class Domains():
        ''' Работа с доменами пользователя '''
        
        class DomainAddError(Exception):
            def __init__(self, login):
                self.login = login
            def __str__(self):
                return 'Domain for login %s was not saved' % self.login
            
        class AlreadyExistsError(Exception):
            pass   
        
        def __init__(self, account):
            assert isinstance(account, Account), "'account' parameter should be an Account instance"
            self.account = account
            self.db = account.db

        def __call__(self):
            return self.list()

        def list(self):
            """ Возвращает список доменов, назначенных данному аккаунту """
            data = self.db.domain.find_one({'login': self.account.login})
            try:
                domains = data['domains']
                assert isinstance(domains, dict)
                domains = [ value for key, value in domains.items()]
                return domains
            except (AssertionError, KeyError, TypeError):
                return []
       
        def list_request(self):
            """ Возвращает список заявок на регистрацию домена данного аккаунта """
            data = self.db.domain.find_one({'login': self.account.login})
            try:
                requests = data['requests']
                assert isinstance(requests, list)
                return requests
            except (AssertionError, KeyError, TypeError):
                return []
           

            
        def add(self, url):
            """ Добавляет домен к списку разрешённых доменов пользователя """
            try:
                domain = url
                if domain.startswith('http://'):
                    domain = domain[7:]
                if domain.startswith('https://'):
                    domain = domain[8:]
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                self.db.domain.update({'login': self.account.login},
                                      {'$set': {('domains.' + str(uuid1())): domain}},
                                               safe=True, upsert=True)
                
            except (pymongo.errors.OperationFailure):
                raise Account.Domains.DomainAddError(self.account.login)
                   
            
        def list_requests(self):
            """ Возвращает список заявок на регистрацию доменов """
            data = self.db.domain.find_one({'login': self.account.login})
            try:
                requests = data['requests']
                assert isinstance(requests, list)
                return requests
            except (AssertionError, KeyError, TypeError):
                return []
            

        def add_request(self, url):
            """ Добавляет заявку на добавление домена """
            print self.list()
            
            if filter(lambda x: x == url or ('http://%s' % x) == url, self.list()):
                raise Account.Domains.AlreadyExistsError()
            
            self.db.domain.update({'login': self.account.login},
                                           {'$addToSet': {'requests': url}},
                                           safe=True, upsert=True)
        
        def approve_request(self, url):
            """ Одобряет заявку на добавление домена """
            # Проверяем, была ли подана такая заявка
            if not self.db.domain.find_one({'login': self.account.login, 'requests': url}):
                return False
            self.add(url)
            self.remove_request(url)
            
        def remove_request(self, url):
            """ Удаляет заявку на добавление домена """
            self.db.domain.update({'login': self.account.login},
                                           {'$pull': {'requests': url}},
                                           safe=True, upsert=True)
        def reject_request(self, url):
            if not self.db.domain.find_one({'login': self.account.login, 'requests': url}):
                return False    
            self.db.domain.update({'login': self.account.login},
                                           {'$addToSet': {'rejected': url}},
                                           safe=True, upsert=True)
            self.remove_request(url)
            
            
        
        
    def get_login(self):
        return self._login 
    def set_login(self, val):
        self._login = val.rstrip()
    login = property(get_login, set_login)
    
    def get_account_type(self):
        if not self.loaded: self.load()
        return self._account_type
    def set_account_type(self, val):
        self._account_type = val
    account_type = property(get_account_type, set_account_type)
    
    User = 'user'
    Manager = 'manager'
    Administrator = 'administrator'

    def __init__(self, login):
        self.login = login
        self.guid = str(uuid1())
        self.email = ''
        self.password = ''
        self.phone = ''
        self.owner_name = ''
        self.min_out_sum = 100
        self.click_percent = 50
        self.click_cost_min = 0.01
        self.click_cost_max = 1.00
        self.imp_percent = 50
        self.imp_cost_min = 0.05
        self.imp_cost_max = 2.00
        self.manager_get = None
        self.registration_date = datetime.datetime.now()
        self.account_type = Account.User 
        self.db = app_globals.db 
        self.report = AccountReports(self)
        self.domains = Account.Domains(self)
        self.loaded = False
        self.money_out_paymentType = []
        self.money_web_z = False
        self.money_card = False
        self.money_factura = False
        self.money_yandex = False
        self.prepayment = False
        
        #: Заблокирован ли аккаунт
        #: Может принимать значения:
        #:     False или '': не заблокирован
        #:     'light': временная приостановка, которую может снять сам пользователь
        #:     'banned': аккаунт заблокирован полностью (за нарушение) 
        self.blocked = False
        
    def register(self):
        ''' Регистрирует пользователя '''
        try:
            assert self.login, 'Login must be specified'
            assert self.db, 'Database connection must be assigned'
            self.db.users.ensure_index('login', unique=True)
            if self.money_web_z:
                self.money_out_paymentType.append(u'webmoney_z')
            if self.money_card:
                self.money_out_paymentType.append(u'card')
            if self.money_factura:
                self.money_out_paymentType.append(u'factura')
            if self.money_yandex:
                self.money_out_paymentType.append(u'yandex')
            cost = {'ALL':{'click':{'percent': int(self.click_percent), 'cost_min': float(self.click_cost_min), 'cost_max': float(self.click_cost_max)},\
                           'imp':{'percent': int(self.imp_percent), 'cost_min': float(self.imp_cost_min), 'cost_max': float(self.imp_cost_max)}}}
            self.db.users.insert({'login': self.login,
                                  'guid': self.guid,
                                  'password': self.password,
                                  'registrationDate': self.registration_date,
                                  'email': self.email,
                                  'phone': self.phone,
                                  'ownerName': self.owner_name,
                                  'cost': cost,
                                  'minOutSum': self.min_out_sum,
                                  'managerGet': self.manager_get,
                                  'manager': self._account_type in (Account.Manager),
                                  'accountType': self._account_type,
                                  'moneyOutPaymentType': self.money_out_paymentType,
                                  'blocked': False
                                  },
                                  safe=True)
            log.info(vars(self))
            self.loaded = True
        except (pymongo.errors.DuplicateKeyError, pymongo.errors.OperationFailure):
            raise Account.AlreadyExistsError(self.login)
        
    def update(self):
        ''' Обновляет данные пользователя'''
        try:
            self.money_out_paymentType = []
            if self.money_web_z:
                self.money_out_paymentType.append(u'webmoney_z')
            if self.money_card:
                self.money_out_paymentType.append(u'card')
            if self.money_factura:
                self.money_out_paymentType.append(u'factura')
            if self.money_yandex:
                self.money_out_paymentType.append(u'yandex')
            self.db.users.update({'login': self.login, 'guid':self.guid},
                                  {'$set':{
                                  'password': self.password,
                                  'registrationDate': self.registration_date,
                                  'email': self.email,
                                  'phone': self.phone,
                                  'ownerName': self.owner_name,
                                  'cost.ALL.click.percent': int(self.click_percent),
                                  'cost.ALL.click.cost_min': float(self.click_cost_min),
                                  'cost.ALL.click.cost_max': float(self.click_cost_max),
                                  'cost.ALL.imp.percent': int(self.imp_percent),
                                  'cost.ALL.imp.cost_min': float(self.imp_cost_min),
                                  'cost.ALL.imp.cost_max': float(self.imp_cost_max),
                                  'minOutSum': self.min_out_sum,
                                  'managerGet': self.manager_get,
                                  'manager': self._account_type in (Account.Manager),
                                  'accountType': self._account_type,
                                  'moneyOutPaymentType': self.money_out_paymentType,
                                  'prepayment': self.prepayment,
                                  'blocked': self.blocked
                                  }},
                                  safe=True)

            # При блокировании менеджера, снимаем ответственного менеджера с сайта
            if self._account_type == Account.Manager and self.blocked == 'banned':
                self.db.users.update({'managerGet': self.login},
                                     {'$set': {'managerGet': ''}},
                                     multi=True)

            mq.MQ().account_update(self.login)
        except:    
            raise Account.UpdateError(self.login)
            

    def load(self):
        ''' Загружает аккаунт '''
        assert self.login, 'Login must be specified'
        
        record = self.db.users.find_one({'login': self.login})
        if not record:
            raise Account.NotFoundError(self.login)
        self.guid = record['guid']
        self.password = record['password']
        self.registration_date = record['registrationDate']
        self.email = record.get('email' ,'')
        self.phone = record.get('phone', '')
        self.owner_name = record.get('ownerName', '')
        self.prepayment = record.get('prepayment', False)
        self.click_percent = int(record.get('cost',{}).get('ALL',{}).get('click',{}).get('percent',50))
        self.click_cost_min = float(record.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_min',  0.01))
        self.click_cost_max = float(record.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_max', 1.00))
        self.imp_percent = int(record.get('cost',{}).get('ALL',{}).get('imp',{}).get('percent',50))
        self.imp_cost_min = float(record.get('cost',{}).get('ALL',{}).get('imp',{}).get('cost_min',  0.05))
        self.imp_cost_max = float(record.get('cost',{}).get('ALL',{}).get('imp',{}).get('cost_max', 2.00))
        try:
            self.min_out_sum = float(record.get('minOutSum', 100))
        except:
            self.min_out_sum = 100
        self.manager_get = record.get('managerGet')
        self.money_out_paymentType = record.get('moneyOutPaymentType') or ['webmoney_z']
        self.blocked = record.get('blocked', False)
        acc_type = record.get('accountType', 'user')
        if acc_type == 'user':              self.account_type = Account.User
        elif acc_type == 'manager':         self.account_type = Account.Manager
        elif acc_type == 'administrator':   self.account_type = Account.Administrator
        else:                               self.account_type = Account.User
        self.loaded = True
    
    
    def informers(self):
        """ Возвращает список информеров данного пользователя """
        result = []
        for object in self.db.informer.find({'user': self.login}):
            informer = Informer.load_from_mongo_record(object)
            result.append(informer)
        return result


    def exists(self):
        """ Возвращает True, если пользователь с данным login существует, иначе False """
        return True if self.db.users.find_one({'login': self.login}) else False 

class AccountReports():
    """ Отчёты по аккаунту пользователя """
    
    def __init__(self, account):
        if isinstance(account, Account):
            self.account = account
        else:
            raise ValueError(), "account should be an Account instance or login string!"
        self.db = app_globals.db
    
    def balance(self): 
        """Возвращает сумму на счету пользователя """
        # Доход
        try:
            income = self.db.stats_daily_adv.group([],
                                              {'user': self.account.login },
                                              {'sum': 0},
                                              'function(o,p) {p.sum += (o.totalCost || 0); }')
            income = float(income[0].get('sum',0))
        except:
            income = 0.0
            
        # Сумма выведенных денег
        try:
            money_out = sum([x.get('summ', 0) for x in self.money_out_requests(approved=True)])
            money_out = float(money_out)
        except:
            money_out = 0.0
        
        return income - money_out

    def money_out_requests(self, approved=None):
        """ Возращает список заявок на вывод средств.
            Если approved == None, то вернёт все заявки.
            Если approved == True, то вернёт только подтверждённые заявки
            Если approved == False, то вернёт только неподтверждённые заявки
        """
        condition = {'user.login': self.account.login}
        if isinstance(approved, bool):
            condition['approved'] = approved
        data = self.db.money_out_request.find(condition)
        return list(data) 


class ManagerReports():
    """ Отчёты по менеджеру """
    
    def __init__(self, account):
        if isinstance(account, Account):
            self.account = account
        else:
            raise ValueError(), "account should be an Account instance or login string!"
        assert account.account_type == Account.Manager, "account_type must be Account.Manager"
        self.db = app_globals.db
    
    def money_out_requests(self, approved=None):
        """ Возращает список заявок на вывод средств.
            Если approved == None, то вернёт все заявки.
            Если approved == True, то вернёт только подтверждённые заявки
            Если approved == False, то вернёт только неподтверждённые заявки
        """
        condition = {'user.login': self.account.login}
        if isinstance(approved, bool):
            condition['approved'] = approved
        data = self.db.money_out_request.find(condition)
        return list(data)
    
    
    def monthProfitPerDate(self):
        ''' Каждодневный доход за последние 30 дней'''
        totalCost = 0
        manager = self.account.login
        dateStart = datetime.datetime.today() - datetime.timedelta(days=30)
        dateEnd = datetime.datetime.today()
        users = [ x['login'] for x in self.db.users.find({'managerGet': manager} )]
        manager_percent =sorted( [{'date': x['date'], 'percent': x['percent']} for x in self.db.manager.percent.find({'login': manager})], reverse=True)
        percent = 0
        
        data = {}
        for x in StatisticReport().statUserGroupedByDate(users, dateStart, dateEnd):
            if not data.get(x['date']):
                data[x['date']] = 0
            for m_p in manager_percent:    
                if x['date'] > m_p['date']:
                    percent = m_p['percent']
                    print percent
                    break
                else:
                    print "Не нашли"
                    print percent
            data[x['date']] += x['tiaser_totalCost'] * (percent / 100.0)
        
        date_sum = []
        for x in sorted(data.keys()):
            date_sum.append((x.strftime('%d.%m.%y'), h.formatMoney(data[x])))
            
        sum = 0
        for x in data.keys():
            sum += data[x]
        userdata = {'date': u'Итого:', 'sum': h.formatMoney(sum)}    
                    
        return h.jgridDataWrapper(date_sum, userdata)         
                
        
    
    def monthBalance(self):
        ''' Возвращает заработок за последние 30 дней'''
        totalCost = 0
        manager = self.account.login
        dateStart = datetime.datetime.today() - datetime.timedelta(days=30)
        dateEnd = datetime.datetime.today()
        users = [ x['login'] for x in self.db.users.find({'managerGet': manager} )]
        manager_percent =sorted( [{'date': x['date'], 'percent': x['percent']} for x in self.db.manager.percent.find({'login': manager})], reverse=True)
        percent = 0
        for x in StatisticReport().statUserGroupedByDate(users, dateStart, dateEnd):
            for m_p in manager_percent:    
                if x['date'] > m_p['date']:
                    percent = m_p['percent']
                    print percent
                    break
                else:
                    print "Не нашли"
                    print percent
            totalCost += x['tiaser_totalCost'] * (percent / 100.0)
        return float(totalCost)
    
    def balance(self):
        """ Возвращает сумму на счету менеджера """
        totalCost = 0
        manager = self.account.login
        users = [ x['login'] for x in self.db.users.find({'managerGet': manager} )]
        manager_percent = [(x['date'], x['percent']) for x in self.db.manager.percent.find({'login': manager})]
        now = datetime.datetime.today()
        one_day = datetime.timedelta(days=1)
        tomorrow = now + one_day
        manager_percent.append((datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0,0,0), 0))
        i = 0  
        for date_percent in sorted(manager_percent, key=lambda row:row[0] ):
            if (i == 0):
                prev_date = date_percent[0]
                percent = date_percent[1]
                i += 1
                continue
            costs = self.db.stats_daily_adv.group([],
                                             {'user': {'$in': users}, 'date': {'$gt': prev_date,'$lt': date_percent[0]}},
                                             {'sum': 0, 'i': 0},
                                             '''function(o,p) {
                                             if (o.isOnClick){
                                             p.sum += o.teaser_totalCost || 0;
                                             p.i +=1 }}''')
            for cost in costs:
                    totalCost += cost['sum'] * percent
            prev_date =  date_percent[0]
            percent = date_percent[1]

        income = float(totalCost) / float(100)
        
        # Сумма выведенных денег
        try:
            money_out = sum([x.get('summ', 0) for x in self.money_out_requests(approved=True)])
            money_out = float(money_out)
        except:
            money_out = 0.0
            
        return income - money_out    
    

    def currentPercent(self):
        """ Возвращает текущий процент менеджера """
        try:
            return self.db.manager.percent.find({'login': self.account.login}).sort('date', pymongo.DESCENDING)[0].get('percent', 0)
        except:
            return 0


class Permission():
    """ Права пользователей """
    
    VIEW_ALL_USERS_STATS = 'view all users stats'       # Может просматривать статистику всех пользователей, а не только тех, кого привёл
    VIEW_MONEY_OUT = 'view money out'                   # Может просматривать историю вывода денежных средств
    USER_DOMAINS_MODERATION = 'user domains moderation' # Может одобрять/отклонять заявки на регистрацию
    SET_CLICK_COST = 'set click cost'                   # Может устанаваливать цену за клик для пользователя
    SET_MANAGER_PERCENT = 'set manager percent'         # Может устанавливать менеджеру  процент от дохода 
    REGISTER_USERS_ACCOUNT = 'register users account'   # Может регистрировать пользовательские аккаунты
    MANAGE_USER_INFORMERS = 'manage user informers'     # Может настраивать информеры пользователей (в т.ч. и расширенные настройки)
    ACCESS_ATTRACTOR = 'access attractor'               # Имеет доступ к Yottos Attractor
    
    class InsufficientRightsError(Exception):
        """ Недостаточно прав для выполнения операции """
        pass
    
    def __init__(self, account):
        assert account and isinstance(account, Account), "'account' must be an Account instance"
        if not account.exists():
            raise Account.NotFoundError(account)
        self.account = account
        self.permissions = set()
        self.db = app_globals.db
        user = self.db.users.find_one({'login': self.account.login})
        for permission in user.get('permissions', []):
            if permission in (self.VIEW_ALL_USERS_STATS,
                              self.VIEW_MONEY_OUT,
                              self.USER_DOMAINS_MODERATION,
                              self.SET_CLICK_COST,
                              self.SET_MANAGER_PERCENT,
                              self.REGISTER_USERS_ACCOUNT,
                              self.MANAGE_USER_INFORMERS,
                              self.ACCESS_ATTRACTOR):
                self.permissions.add(permission)
                
                
    def has(self, right):
        ''' Возвращает ``True``, если пользователь имеет данное разрешение, иначе ``False`` '''
        if self.account.account_type == Account.Administrator:
            return True
        if right in self.permissions:
            return True
        return False
    

    def grant_to(self, account, permission):
        'Выдаёт разрешение ``permission`` аккаунту ``account`` (только в том случае, если дающий разрешение сам его имеет)'
        assert account and isinstance(account, Account), "'account' must be an Account instance"
        if not account.exists():
            raise Account.NotFoundError(account)
        if not self.has(permission):
            raise Permission.InsufficientRightsError
        self.db.users.update({'login': account.login},
                             {'$addToSet': {'permissions': permission}},
                             safe=True)
        self.permissions.add(permission)

