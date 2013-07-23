# This Python file uses the following encoding: utf-8
from datetime import datetime
from ftplib import FTP
from getmyad.lib.helpers import progressBar
from pylons import app_globals, config
from pymongo import Connection, ASCENDING, DESCENDING
from uuid import uuid1
import StringIO
import getmyad
import getmyad.lib.helpers as h
import pymongo
import re


class Options():
    try:
        db = app_globals.db
    except:
        db = None

conn = Connection()
db = conn.getmyad_db


def advertiseScriptSummary(adv_id, dateStart = None, dateEnd = None):
    ''' Возвращает итоги по рекламной выгрузке adv_id.
        Параметры dateStart или dateEnd являются фильтрами, если заданы''' 
    global db
    reduce = 'function(o,p) {' \
        '    p.clicks += isNaN(o.clicks)? 0 : o.clicks;' \
        '    p.unique += isNaN(o.clicksUnique)? 0 : o.clicksUnique;' \
        '    p.impressions += isNaN(o.impressions)? 0 : o.impressions;' \
        '}' 
    condition = {'adv': adv_id}
    dateCondition = {}
    if dateStart <> None: dateCondition['$gte'] = dateStart
    if dateEnd <> None:   dateCondition['$lte'] = dateEnd
    if len(dateCondition) > 0:
        condition['date'] = dateCondition
    
    return db.stats_daily.group(['adv', 'lot.title'],
                                condition,
                                {'clicks':0, 'unique':0, 'impressions':0},
                                reduce)
      
    
    
    
def allAdvertiseScriptsSummary(user_login, dateStart = None, dateEnd = None):
    """Возвращает суммарную статистику по всем площадкам пользователя user_id"""
    global db
    ads = {}
    for t in [{x['guid'] : x['title']} for x in db.Advertise.find({"user.login": user_login})]:
        ads.update(t)
    
    reduce = 'function(o,p) {' \
        '    p.clicks += o.clicks || 0;' \
        '    p.unique += o.clicksUnique || 0;' \
        '    p.impressions += o.impressions || 0;' \
        '    p.totalCost += o.totalCost || 0;' \
        '}' 
    condition = {'adv': {'$in': ads.keys()}}
    dateCondition = {}
    if dateStart <> None: dateCondition['$gte'] = dateStart
    if dateEnd <> None:   dateCondition['$lte'] = dateEnd
    if len(dateCondition) > 0:
        condition['date'] = dateCondition
    
    res = db.stats_daily_adv.group(['adv'],
                                   condition,
                                   {'clicks':0, 'unique':0, 'impressions':0, 'totalCost':0},
                                   reduce)
    for x in res:
        x['advTitle'] = ads[x['adv']]
    
    return res



def statGroupedByDate(adv_guid, dateStart = None, dateEnd = None):
    """Возвращает список {дата,уникальных,кликов,показов,сумма} для одной или нескольких выгрузок.
    adv_guid может быть или строкой или списком строк""" 
    reduce = 'function(o,p) {' \
        '    p.clicks += o.clicks || 0;' \
        '    p.unique += o.clicksUnique || 0;' \
        '    p.impressions += o.impressions || 0;' \
        '    p.summ += o.totalCost || 0;' \
        '}' 
    
    condition = {'adv': {'$in': adv_guid if isinstance(adv_guid, list) else [adv_guid]}}
    dateCondition = {}
    if dateStart <> None: dateCondition['$gte'] = dateStart
    if dateEnd <> None:   dateCondition['$lte'] = dateEnd
    if len(dateCondition) > 0:
        condition['date'] = dateCondition

    return [{'date': x['date'],
             'unique': x['unique'],
             'clicks': x['clicks'],
             'impressions': x['impressions'],
             'summ': x['summ']}
             for x in db.stats_daily_adv.group(['date'],
                                               condition,
                                               {'clicks':0, 'unique':0, 'impressions':0, 'summ':0},
                                               reduce)]

def updateTime():
    """Возвращает последнее время обновления статистики"""
    date = app_globals.db.config.find_one({'key': 'impressions last date'}).get('value')
    return date if isinstance(date, datetime) else None


def users():
    """Возвращает список пользователей GetMyAd"""
    return [{
             'guid': x.get('guid'),
             'login': x['login'],
             'title': x.get('title'),
             'registrationDate': x['registrationDate'],
             'manager': x.get('manager', False)
            }
             for x in app_globals.db.users.find()]



def currentClickCost():
    """Текущие расценки для каждого пользователя"""
    for user in users():
        if user['manager']:
            continue
        cursor = db.click_cost.find({'user.login': user['login']}).sort('date', DESCENDING).limit(1)
        if cursor.count() > 0:
            cost = cursor[0]
            yield { 'date': cost['date'],
                    'user_login': cost['user']['login'],
                    'cost': cost['cost']
                  }
        else:
            yield { 'date': None,
                    'user_login': user['login'],
                    'cost': 0
                  }

def setClickCost(cost, user_login, user_guid, date):
    """Устанавливает цену за клик click_cost для пользователя user начиная со времени date"""
    db.click_cost.update({'date': date,
                          'user': {'guid': user_guid,
                                   'login': user_login}},
                         {'$set': {'cost': cost}},
                         upsert=True)

def setManagerPercent(manager_login, percent):
    """ Устанавливает процент менеджера"""
    app_globals.db.users.update({'login': manager_login}, {'$set':{'percent': percent}})
    now = datetime.today()
    today = datetime(now.year, now.month, now.day, 0,0,0)
    app_globals.db.manager.percent.update({'date': today,
                                          'login': manager_login},
                                           {'$set': {'percent':percent}},
                                           upsert = True)


def accountPeriodSumm(dateCond, user_login):
    ads = [x['guid'] for x in db.Advertise.find({'user.login': user_login})]                                       
    income = db.stats_daily_adv.group([],
                                      {'adv': {'$in': ads}, 'date': dateCond},
                                      {'sum': 0},
                                      'function(o,p) {p.sum += isNaN(o.totalCost)? 0 : o.totalCost;}')
    try:
        income = float(income[0].get('sum', 0))
    except:
        income = 0
    return income




def moneyOutApproved(user_login):
    """Возвращает список одобренных заявок"""
    return db.money_out_request.find({'user.login': user_login,
                                      'approved': True}).sort('date', ASCENDING)
    
    
    
    
    
    
    
class Informer:
    """ Рекламный информер (он же рекламный скрипт, рекламная выгрузка) """ 
    
    def __init__(self):
        self.guid = None
        self.title = None
        self.admaker = None
        self.css = None
        self.user_login = None
        self.non_relevant = None
        self.domain = None
        
    
    def save(self):
        """ Сохраняет информер, при необходимости создаёт """
        update = {}
        if self.guid: update['guid'] = self.guid
        if self.title: update['title'] = self.title
        if self.admaker: update['admaker'] = self.admaker
        if self.css: update['css'] = self.css
        if self.user_login: update['user.login'] = self.user_login
        if self.domain: update['domain'] = self.domain
        if isinstance(self.non_relevant, dict) \
                        and 'action' in self.non_relevant \
                        and 'usercode' in self.non_relevant:
            update['nonRelevant'] = {'action': self.non_relevant['action'],
                                     'usercode': self.non_relevant['usercode']}
        update['lastModified'] = datetime.now()
        
        if not self.guid:
            # Создание нового информера
            if not self.user_login:
                raise ValueError('User login must be specified when creating informer!')
            self.guid = str(uuid1()).upper()
            import pyodbc
            conn = pyodbc.connect(config.get("mssql_connection_string"), autocommit=True)
            cursor = conn.cursor()
            cursor.execute("insert into Scripts(ScriptID, Title, UserLogin) values (?,?,?)",
                           (self.guid, self.title, self.user_login))
         
        app_globals.db.Advertise.update({'guid': self.guid},
                                        {'$set': update},
                                        upsert=True)
        uploader = InformerFtpUploader()
        uploader.upload(self.guid)
    
    
    def load(self, id):
        pass


    @staticmethod
    def load_from_mongo_record(mongo_record):
        """ Загружает информер из записи MongoDB """
        informer = Informer()
        informer.guid = mongo_record['guid']
        informer.title = mongo_record['title']
        informer.user_login = mongo_record["user"]['login']
        informer.admaker = mongo_record.get('admaker')
        informer.css = mongo_record.get('css')
        informer.domain = mongo_record.get('domain')
        if 'nonRelevant' in mongo_record:
            informer.non_relevant = {}
            informer.non_relevant['action'] = mongo_record['nonRelevant']['action']
            informer.non_relevant['usercode'] = mongo_record['nonRelevant']['usercode']
        return informer



class InformerFtpUploader:
    """ Заливает javascript отображения информера на FTP-сервер """
    
    def __init__(self):
        self.url = 'plesk2.dc.utel.ua'
        self.login = 'zcdnyott1709com'
        self.password = 'D%l)s2v6'
        self.ftp = None
        self.db = app_globals.db
        
        
    def __del__(self):
        self.disconnect()
        
    
    def connect(self):
        """ Подключается к FTP серверу """
        self.ftp = FTP(self.url)
        self.ftp.login(self.login, self.password)
        self.ftp.cwd('httpdocs')
        self.ftp.cwd('getmyad')
    
    
    def upload(self, informer_id):
        """ Загружает на FTP скрипт составления информера informer_id """
        if not self.ftp:
            self.connect()
        adv = self.db.Advertise.find_one({'guid': informer_id})
        if not adv:
            return False
        try:
            guid = adv['guid']
            width = int(re.match('[0-9]+', adv['admaker']['Main']['width']).group(0))
            height = int(re.match('[0-9]+', adv['admaker']['Main']['height']).group(0))
        except:
            raise Exception("Incorrect size dimensions for informer %s" % guid)
        try:
            border = int(re.match('[0-9]+', adv['admaker']['Main']['borderWidth']).group(0))
        except:
            border = 1
        width += border*2
        height += border*2 

        informer = StringIO.StringIO()
        informer.write("""
;document.write("<iframe src='http://rynok.yottos.com.ua/p_export.aspx?scr=%s&" + 
encodeURIComponent(window.location.host) + "' width='%s' height='%s'  frameborder='0' scrolling='no'></iframe>");
""" 
                       % (guid, width, height))
        informer.seek(0)
        self.ftp.storlines('STOR %s.js' % guid, informer)
        informer.close()
        
        
    def uploadAll(self):
        """ Загружает на FTP скрипты для всех информеров """
        advertises = db.Advertise.find({}, {'guid': 1})
        prog = progressBar(0, advertises.count())
        i = 0
        for adv in advertises:
            i+= 1
            prog.updateAmount(i)
            print "Saving informer %s... \t\t\t %s" % (adv['guid'], prog)
            
            self.upload(adv['guid'])

    
    def disconnect(self):
        """ Отключение от FTP-сервера """
        if self.ftp:
            self.ftp.quit()




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
        
    
    class Domains():
        ''' Работа с доменами пользователя '''
        def __init__(self, account):
            assert isinstance(account, Account), "'account' parameter should be an Account instance"
            self.account = account
            self.db = account.db
            
        def __call__(self):
            return self.list()

        def list(self):
            """ Возвращает список доменов, назначенных данному аккаунту """
            data = self.db['user.domains'].find_one({'login': self.account.login})
            try:
                domains = data['domains']
                assert isinstance(domains, list)
                return domains
            except (AssertionError, KeyError, TypeError):
                return []
       
        def list_request(self):
            """ Возвращает список заявок на регистрацию домена данного аккаунта """
            data = self.db['user.domains'].find_one({'login': self.account.login})
            try:
                requests = data['requests']
                assert isinstance(requests, list)
                return requests
            except (AssertionError, KeyError, TypeError):
                return []
           

            
        def add(self, url):
            """ Добавляет домен к списку разрешённых доменов пользователя """
            '702 557 996, 8269'
            domain = url
            if domain.startswith('http://'):
                domain = domain[7:]
            if domain.startswith('https://'):
                domain = domain[8:]
            if domain.startswith('www.'):
                domain = domain[4:]
            
            self.db['user.domains'].update({'login': self.account.login},
                                           {'$addToSet': {'domains': domain}},
                                           safe=True, upsert=True)
            
        def list_requests(self):
            """ Возвращает список заявок на регистрацию доменов """
            data = self.db['user.domains'].find_one({'login': self.account.login})
            try:
                requests = data['requests']
                assert isinstance(requests, list)
                return requests
            except (AssertionError, KeyError, TypeError):
                return []
            

        def add_request(self, url):
            """ Добавляет заявку на добавление домена """
            self.db['user.domains'].update({'login': self.account.login},
                                           {'$addToSet': {'requests': url}},
                                           safe=True, upsert=True)
        
        def approve_request(self, url):
            """ Одобряет заявку на добавление домена """
            # Проверяем, была ли подана такая заявка
            if not self.db['user.domains'].find_one({'login': self.account.login, 'requests': url}):
                return False
            self.remove_request(url)
            self.add(url)
            
        def remove_request(self, url):
            """ Удаляет заявку на добавление домена """
            self.db['user.domains'].update({'login': self.account.login},
                                           {'$pull': {'requests': url}},
                                           safe=True, upsert=True)
            
        
        
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
        self.email = ''
        self.password = ''
        self.phone = ''
        self.owner_name = ''
        self.min_out_sum = 100
        self.manager_get = None
        self.registration_date = datetime.now()
        self.account_type = Account.User 
        
        self.db = Options.db 
        self.report = AccountReports(self)
        self.domains = Account.Domains(self)
        self.loaded = False
        
        
    def register(self):
        ''' Регистрирует пользователя '''
        try:
            assert self.login, 'Login must be specified'
            assert self.db, 'Database connection must be assigned'
            self.db.users.ensure_index('login', unique=True)
            self.db.users.insert({'login': self.login,
                                  'password': self.password,
                                  'registrationDate': self.registration_date,
                                  'email': self.email,
                                  'phone': self.phone,
                                  'ownerName': self.owner_name,
                                  'minOutSum': self.min_out_sum,
                                  'managerGet': self.manager_get,
                                  'manager': self._account_type in (Account.User, Account.Manager),
                                  'accountType': self._account_type
                                  }, safe=True)
            self.loaded = True
        except (pymongo.errors.DuplicateKeyError, pymongo.errors.OperationFailure):
            raise Account.AlreadyExistsError(self.login)


    def load(self):
        ''' Загружает аккаунт '''
        assert self.login, 'Login must be specified'
        
        record = self.db.users.find_one({'login': self.login})
        if not record:
            raise Account.NotFoundError(self.login)
        self.password = record['password']
        self.registration_date = record['registrationDate']
        self.email = record.get('email' ,'')
        self.phone = record.get('phone', '')
        self.owner_name = record.get('ownerName', '')
        self.min_out_sum = record.get('minOutSum', 100)
        self.manager_get = record.get('managerGet')
        acc_type = record.get('accountType', 'user')
        if acc_type == 'user':              self.account_type = Account.User
        elif acc_type == 'manager':         self.account_type = Account.Manager
        elif acc_type == 'administrator':   self.account_type = Account.Administrator
        else:                               self.account_type = Account.User
        self.loaded = True
    
    
    def informers(self):
        """ Возвращает список информеров данного пользователя """
        result = []
        for object in db.Advertise.find({'user.login': self.login}):
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
        self.db = Options.db
    
    
    def balance(self): 
        """Возвращает сумму на счету пользователя """
        # Доход
        try:
            ads = [x.guid for x in self.account.informers()]
            income = db.stats_daily_adv.group([],
                                              {'adv': {'$in': ads}},
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
        return [x for x in data] # h.cursor_to_list(data)



class Permission():
    """ Права пользователей """
    
    VIEW_ALL_USERS_STATS = 'view all users stats'       # Может просматривать статистику всех пользователей, а не только тех, кого привёл
    VIEW_MONEY_OUT = 'view money out'                   # Может просматривать историю вывода денежных средств
    USER_DOMAINS_MODERATION = 'user domains moderation' # Может одобрять/отклонять заявки на регистрацию
    SET_CLICK_COST = 'set click cost'                   # Может устанаваливать цену за клик для пользователя
    SET_MANAGER_PERCENT = 'set manager percent'         # Может устанавливать менеджеру  процент от дохода 
    REGISTER_USERS_ACCOUNT = 'register users account'    # Может регистрировать пользовательские аккаунты
     
    
    class InsufficientRightsError(Exception):
        """ Недостаточно прав для выполнения операции """
        pass
    
    def __init__(self, account):
        assert account and isinstance(account, Account), "'account' must be an Account instance"
        if not account.exists():
            raise Account.NotFoundError
        self.account = account
        self.permissions = set()
        self.db = Options.db
        user = self.db.users.find_one({'login': self.account.login})
        for permission in user.get('permissions', []):
            if permission == self.VIEW_ALL_USERS_STATS:
                self.permissions.add(self.VIEW_ALL_USERS_STATS)
            elif permission == self.VIEW_MONEY_OUT:
                self.permissions.add(self.VIEW_MONEY_OUT) 
            elif permission == self.USER_DOMAINS_MODERATION:
                self.permissions.add(self.USER_DOMAINS_MODERATION)
            elif permission == self.SET_CLICK_COST:
                self.permissions.add(self.SET_CLICK_COST)
            elif permission == self.SET_MANAGER_PERCENT:
                self.permissions.add(self.SET_MANAGER_PERCENT)
            elif permission == self.REGISTER_USERS_ACCOUNT:
                self.permissions.add(self.REGISTER_USERS_ACCOUNT)
                
                
    def has(self, right):
        ''' Возвращает True, если пользователь имеет данное разрешение, иначе False '''
        if self.account.account_type == Account.Administrator:
            return True
        if right in self.permissions:
            return True
        return False
    

    def grant_to(self, account, permission):
        ''' Выдаёт разрешение permission аккаунту account (только в том случае, если дающий разрешение сам его имеет) '''
        assert account and isinstance(account, Account), "'account' must be an Account instance"
        if not account.exists():
            raise Account.NotFoundError
        if not self.has(permission):
             raise Permission.InsufficientRightsError
        self.db.users.update({'login': account.login},
                             {'$addToSet': {'permissions': permission}},
                             safe=True)
        self.permissions.add(permission)
