# This Python file uses the following encoding: utf-8
from datetime import datetime, timedelta
from ftplib import FTP
from getmyad.config.social_ads import social_ads
from getmyad.lib.helpers import progressBar
from pylons import app_globals, config
from pymongo import ASCENDING, DESCENDING
from uuid import uuid1
import StringIO
import getmyad
import getmyad.lib.helpers as h
import logging
import mq
import pymongo
import re

class Options():
    try:
        db = app_globals.db
    except:
        db = None

db = app_globals.db


def makePassword():
    """Возвращает сгенерированный пароль"""
    from random import Random
    rng = Random()

    righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
    lefthand = '789yuiophjknmYUIPHJKLNM'
    allchars = righthand + lefthand
    
    passwordLength = 8
    alternate_hands = True
    password = ''
    
    for i in range(passwordLength):
        if not alternate_hands:
            password += rng.choice(allchars)
        else:
            if i % 2:
                password += rng.choice(lefthand)
            else:
                password += rng.choice(righthand)
    return password

    
def allAdvertiseScriptsSummary(user_login, dateStart = None, dateEnd = None):
    """Возвращает суммарную статистику по всем площадкам пользователя user_id"""
    global db
    ads = {}
    for t in [{x['guid'] : x.get('domain', '') + ', ' + x['title']} for x in db.informer.find({"user": user_login})]:
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
    """ Возвращает список {дата,уникальных,кликов,показов,сумма} 
        для одной или нескольких выгрузок.
        
        Формат одной структуры в списке:
        
            {'date': datetime.datetime,
             'unique': int,
             'clicks': int,
             'impressions': int,
             'summ': float}
    
        Параметр adv_guid -- коды одного или нескольких информеров,
        по которым будет считаться статистика. Может быть строкой 
        или списком строк
    """
     
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
             for x in app_globals.db.users.find().sort('registrationDate')]



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
    ''' Возвращает сумму аккаунта за период заданный в dateCond'''
    ads = [x['guid'] for x in db.informer.find({'user': user_login})]                                       
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
        if self.domain: update['domain'] = self.domain
        if isinstance(self.non_relevant, dict) \
                        and 'action' in self.non_relevant \
                        and 'userCode' in self.non_relevant:
            update['nonRelevant'] = {'action': self.non_relevant['action'],
                                     'userCode': self.non_relevant['userCode']}
        update['lastModified'] = datetime.now()
        
        if not self.guid:
            # Создание нового информера
            if not self.user_login:
                raise ValueError('User login must be specified when creating informer!')
            self.guid = str(uuid1()).lower()
            update['user'] = self.user_login
        else:
            if self.user_login:
                pass        # TODO: Выдавать предупреждение, что для 
                            # уже созданных информеров нельзя менять пользователя
         
        app_globals.db.informer.update({'guid': self.guid},
                                       {'$set': update},
                                       upsert=True,
                                       safe=True)
        InformerFtpUploader(self.guid).upload()
        mq.MQ().informer_update(self.guid)
        
    def load(self, id):
        raise NotImplementedError

    @staticmethod
    def load_from_mongo_record(mongo_record):
        """ Загружает информер из записи MongoDB """
        informer = Informer()
        informer.guid = mongo_record['guid']
        informer.title = mongo_record['title']
        informer.user_login = mongo_record["user"]
        informer.admaker = mongo_record.get('admaker')
        informer.css = mongo_record.get('css')
        informer.domain = mongo_record.get('domain')
        if 'nonRelevant' in mongo_record:
            informer.non_relevant = {}
            informer.non_relevant['action'] = mongo_record['nonRelevant'].get('action', 'social')
            informer.non_relevant['userCode'] = mongo_record['nonRelevant'].get('userCode', '')
        return informer


class InformerFtpUploader:
    """ Заливает необходимое для работы информера файлы на сервер раздачи статики:
        
        1. Javascript-загрузчик информера.
        2. Статическую заглушку с социальной рекламой на случай отказа GetMyAd.
    """
    
    def __init__(self, informer_id):
        self.informer_id = informer_id
        
    def upload(self):
        """ Заливает через FTP загрузчик и заглушку информера ``informer_id`` """
        self.upload_loader()
        self.upload_reserve()

    def upload_loader(self):
        ' Заливает загрузчик информера '
        if config.get('informer_loader_ftp'):
            try:
                ftp = FTP(host=config.get('informer_loader_ftp'),
                          user=config.get('informer_loader_ftp_user'),
                          passwd=config.get('informer_loader_ftp_password'))
                ftp.cwd(config.get('informer_loader_ftp_path'))
                loader = StringIO.StringIO()
                loader.write(self._generate_informer_loader())
                loader.seek(0)
                ftp.storlines('STOR %s.js' % self.informer_id, loader)
                ftp.quit()
                loader.close()
            except Exception, ex:
                logging.error(ex)
        else:
            logging.warning('informer_loader_ftp settings not set! Check .ini file.')

    def upload_reserve(self):
        ' Заливает заглушку для информера '
        if config.get('reserve_ftp'):
            try:
                ftp = FTP(config.get('reserve_ftp'))
                ftp.login(config.get('reserve_ftp_user'), config.get('reserve_ftp_password'))
                ftp.cwd(config.get('reserve_ftp_path'))
                data = StringIO.StringIO()
                data.write(self._generate_social_ads().encode('utf-8'))
                data.seek(0)
                ftp.storlines('STOR emergency-%s.html' % self.informer_id, data)
                ftp.quit()
                data.close()
            except Exception, ex:
                logging.error(ex)
        else:
            logging.warning('reserve_ftp settings not set! Check .ini file.')
    
    def uploadAll(self):
        """ Загружает на FTP скрипты для всех информеров """
        advertises = db.informer.find({}, {'guid': 1})
        prog = progressBar(0, advertises.count())
        i = 0
        for adv in advertises:
            i+= 1
            prog.updateAmount(i)
#            print "Saving informer %s... \t\t\t %s" % (adv['guid'], prog)
            InformerFtpUploader(adv['guid']).upload()
            
    def _generate_informer_loader(self):
        ''' Возвращает код javascript-загрузчика информера '''
        adv = app_globals.db.informer.find_one({'guid': self.informer_id})
        if not adv:
            return False
        try:
            guid = adv['guid']
            width = int(re.match('[0-9]+', adv['admaker']['Main']['width']).group(0))
            height = int(re.match('[0-9]+', adv['admaker']['Main']['height']).group(0))
        except:
            raise Exception("Incorrect size dimensions for informer %s" % self.informer_id)
        try:
            border = int(re.match('[0-9]+', adv['admaker']['Main']['borderWidth']).group(0))
        except:
            border = 1
        width += border * 2
        height += border * 2 
        return (""";document.write("<iframe src='http://rg.yottos.com/adshow.fcgi?scr=%s&location=" + """ +
                """encodeURIComponent(window.location.href) + "&referrer=" + encodeURIComponent(document.referrer) + "' width='%s' height='%s'  frameborder='0' scrolling='no'></iframe>");"""
                ) % (guid, width, height)
        

    def _generate_social_ads(self):
        ''' Возвращает HTML-код заглушки с социальной рекламой,
            которая будет показана при падении сервиса 
        '''
        inf = app_globals.db.informer.find_one({'guid': self.informer_id})
        if not inf:
            return
        
        try:
            items_count = int(inf['admaker']['Main']['itemsNumber'])
        except:
            items_count = 0 
        
        offers = ''
        for i in xrange(0, items_count):
            adv = social_ads[i % len(social_ads)]
            
            offers += ('''<div class="advBlock"><a class="advHeader" href="%(url)s" target="_blank">''' +
                       '''%(title)s</a><a class="advDescription" href="%(url)s" target="_blank">''' +
                       '''%(description)s</a><a class="advCost" href="%(url)s" target="_blank"></a>''' +
                       '''<a href="%(url)s" target="_blank"><img class="advImage" src="%(img)s" alt="%(title)s"/></a></div>'''
                       ) % {'url': adv['url'], 'title': adv['title'], 'description': adv['description'], 'img': adv['image']}
        return '''
<html><head><META http-equiv="Content-Type" content="text/html; charset=utf-8"><meta name="robots" content="nofollow" /><style type="text/css">html, body { padding: 0; margin: 0; border: 0; }</style><!--[if lte IE 6]><script type="text/javascript" src="http://cdn.yottos.com/getmyad/supersleight-min.js"></script><![endif]-->
%(css)s
</head>
<body>
<div id='mainContainer'><div id="ads" style="position: absolute; left:0; top: 0">
%(offers)s
</div><div id='adInfo'><a href="http://yottos.com.ua" target="_blank"></a></div>
</body>
</html>''' % {'css': inf.get('css'), 'offers': offers}



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
            try:
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
            
            except (pymongo.errors.OperationFailure):
                raise Account.Domains.DomainAddError(self.account.login)
                   
            
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
            print self.list()
            
            if filter(lambda x: x == url or ('http://%s' % x) == url, self.list()):
                raise Account.Domains.AlreadyExistsError()
            
#            if url.lower() in [x.lower() for x in self.list()]:            
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
        def reject_request(self, url):
            if not self.db['user.domains'].find_one({'login': self.account.login, 'requests': url}):
                return False    
            self.db['user.domains'].update({'login': self.account.login},
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
        self.money_out_paymentType = []
        self.money_web_z = False
        self.money_card = False
        self.money_factura = False
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
            self.db.users.insert({'login': self.login,
                                  'password': self.password,
                                  'registrationDate': self.registration_date,
                                  'email': self.email,
                                  'phone': self.phone,
                                  'ownerName': self.owner_name,
                                  'minOutSum': self.min_out_sum,
                                  'managerGet': self.manager_get,
                                  'manager': self._account_type in (Account.Manager),
                                  'accountType': self._account_type,
                                  'moneyOutPaymentType': self.money_out_paymentType,
                                  'blocked': False
                                  },
                                  safe=True)
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
            self.db.users.update({'login': self.login},
                                  {'$set':{
                                  'password': self.password,
                                  'registrationDate': self.registration_date,
                                  'email': self.email,
                                  'phone': self.phone,
                                  'ownerName': self.owner_name,
                                  'minOutSum': self.min_out_sum,
                                  'managerGet': self.manager_get,
                                  'manager': self._account_type in (Account.Manager),
                                  'accountType': self._account_type,
                                  'moneyOutPaymentType': self.money_out_paymentType,
                                  'prepayment': self.prepayment,
                                  'blocked': self.blocked
                                  }},
                                  safe=True)
            mq.MQ().account_update(self.login)
        except:    
            raise Account.UpdateError(self.login)
            

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
        self.prepayment = record.get('prepayment', False)
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
        for object in db.informer.find({'user': self.login}):
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


class ManagerReports():
    """ Отчёты по менеджеру """
    
    def __init__(self, account):
        if isinstance(account, Account):
            self.account = account
        else:
            raise ValueError(), "account should be an Account instance or login string!"
        assert account.account_type == Account.Manager, "account_type must be Account.Manager"
        self.db = Options.db
    
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
    
    
    def monthProfitPerDate(self):
        ''' Каждодневный доход за последние 30 дней'''
        totalCost = 0
        manager = self.account.login
        users = [ x['login'] for x in db.users.find({'managerGet': manager} )]
        advs = [x['guid'] for x in db.informer.find({'user' : {'$in': users}})]
        manager_percent =sorted( [{'date': x['date'], 'percent': x['percent']} for x in db.manager.percent.find({'login': manager})], reverse=True)
        percent = 0
        
        dateStart = datetime.today() - timedelta(days=30)
        dateEnd = datetime.today()
        data = {}
        for adv in advs:
            for x in statGroupedByDate(adv, dateStart, dateEnd):
                if not data.get(x['date']):
                    data[x['date']] = 0
                for m_p in manager_percent:    
                    if x['date'] > m_p['date']:
                        percent = m_p['percent']
                        break
                data[x['date']] += x['summ'] * percent / 100.0
        
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
        users = [ x['login'] for x in db.users.find({'managerGet': manager} )]
        advs = [x['guid'] for x in db.informer.find({'user' : {'$in': users}})]
        manager_percent = [(x['date'], x['percent']) for x in db.manager.percent.find({'login': manager})]
        now = datetime.today()
        one_day = timedelta(days=1)
        month = timedelta(days=30)
        tomorrow = now + one_day
        month_ago = now - month
        manager_percent.append((datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0,0,0), 0))
        i = 0  
        for date_percent in sorted(manager_percent, key=lambda row:row[0] ):
            if (i == 0):
                prev_date = date_percent[0]
                if prev_date < month_ago:
                    prev_date = month_ago
                percent = date_percent[1]
                i += 1
                continue
            costs = db.stats_daily_adv.group([],
                                             {'adv': {'$in': advs}, 'date': {'$gt': prev_date,'$lt': date_percent[0]}},
                                             {'sum': 0, 'i': 0},
                                             'function(o,p) {p.sum += o.totalCost || 0; p.i +=1 }')
            for cost in costs:
                    totalCost += cost['sum'] * percent
            prev_date =  date_percent[0]
            percent = date_percent[1]

        income = float(totalCost) / float(100)

        return income
    
    def balance(self):
        """ Возвращает сумму на счету менеджера """
        totalCost = 0
        manager = self.account.login
        users = [ x['login'] for x in db.users.find({'managerGet': manager} )]
        advs = [x['guid'] for x in db.informer.find({'user' : {'$in': users}})]
        manager_percent = [(x['date'], x['percent']) for x in db.manager.percent.find({'login': manager})]
        now = datetime.today()
        one_day = timedelta(days=1)
        tomorrow = now + one_day
        manager_percent.append((datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0,0,0), 0))
        i = 0  
        for date_percent in sorted(manager_percent, key=lambda row:row[0] ):
            if (i == 0):
                prev_date = date_percent[0]
                percent = date_percent[1]
                i += 1
                continue
            costs = db.stats_daily_adv.group([],
                                             {'adv': {'$in': advs}, 'date': {'$gt': prev_date,'$lt': date_percent[0]}},
                                             {'sum': 0, 'i': 0},
                                             'function(o,p) {p.sum += o.totalCost || 0; p.i +=1 }')
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
            return db.manager.percent.find({'login': self.account.login}).sort('date', pymongo.DESCENDING)[0].get('percent', 0)
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
            if permission in (self.VIEW_ALL_USERS_STATS,
                              self.VIEW_MONEY_OUT,
                              self.USER_DOMAINS_MODERATION,
                              self.SET_CLICK_COST,
                              self.SET_MANAGER_PERCENT,
                              self.REGISTER_USERS_ACCOUNT,
                              self.MANAGE_USER_INFORMERS):
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
            raise Account.NotFoundError
        if not self.has(permission):
            raise Permission.InsufficientRightsError
        self.db.users.update({'login': account.login},
                             {'$addToSet': {'permissions': permission}},
                             safe=True)
        self.permissions.add(permission)



class Campaign(object):
    "Класс описывает рекламную кампанию, запущенную в GetMyAd"
    
    class NotFoundError(Exception):
        'Кампания не найдена'
        def __init__(self, id):
            self.id = id
        
    
    def __init__(self, id):
        #: ID кампании
        self.id = id.lower()
        #: Заголовок рекламной кампании
        self.title = ''
        #: Является ли кампания социальной рекламой
        self.social = False
        #: Время последнего обновления (см. rpc/campaign.update())
        self.last_update = None
        
        
    def load(self):
        'Загружает кампанию из базы данных'
        c = app_globals.db.campaign.find_one({'guid': self.id})
        if not c:
            raise Campaign.NotFoundError(self.id)
        self.id = c['guid']
        self.title = c.get('title')
        self.social = c.get('social', False)
        self.last_update = c.get('lastUpdate', None)
    
    def restore_from_archive(self):
        'Пытается восстановить кампанию из архива. Возвращает true в случае успеха'
        c = app_globals.db.campaign.archive.find_one({'guid': self.id})
        if not c:
            return False
        self.delete()
        app_globals.db.campaign.save(c)
        app_globals.db.campaign.archive.remove({'guid': self.id}, safe=True)
    
    def save(self):
        'Сохраняет кампанию в базу данных'
        app_globals.db.campaign.update({'guid': self.id},
                                       {'$set': {'title': self.title,
                                                 'social': self.social,
                                                 'lastUpdate': self.last_update}},
                                       upsert=True, safe=True)
    
    def exists(self):
        'Возвращает ``True``, если кампания с заданным ``id`` существует'
        return (app_globals.db.campaign.find_one({'guid': self.id}) <> None)

    def delete(self):
        'Удаляет кампанию'
        app_globals.db.campaign.remove({'guid': self.id}, safe=True)
    
    def move_to_archive(self):
        'Перемещает кампанию в архив'
        c = app_globals.db.campaign.find_one({'guid': self.id})
        if not c: return
        app_globals.db.campaign.archive.remove({'guid': self.id})
        app_globals.db.campaign.archive.save(c, safe=True)
        self.delete()

class Offer(object):
    'Класс описывает рекламное предложение'
    
    def __init__(self, id):
        self.id = id.lower()
        self.title = ''
        self.price = ''
        self.url = ''
        self.image = ''
        self.description = ''
        self.date_added = None
        self.campaign = ''
    
    def save(self):
        'Сохраняет предложение в базу данных'
        app_globals.db.offer.update({'guid': self.id},
                                    {'$set': {'title': self._trim_by_words(self.title, 35),
                                              'price': self.price,
                                              'url': self.url,
                                              'image': self.image,
                                              'description': self._trim_by_words(self.description, 70),
                                              'dateAdded': self.date_added,
                                              'campaignId': self.campaign
                                              }},
                                    upsert=True, safe=True)

    def _trim_by_words(self, str, max_len):
        ''' Обрезает строку ``str`` до длины не более ``max_len`` с учётом слов '''
        if len(str) <= max_len:
            return str
        trimmed_simple = str[:max_len]
        trimmed_by_words = trimmed_simple.rpartition(' ')[0]
        return u'%s…' % (trimmed_by_words or trimmed_simple)
