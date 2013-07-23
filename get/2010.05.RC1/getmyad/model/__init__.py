# This Python file uses the following encoding: utf-8
from pymongo import Connection, ASCENDING, DESCENDING
from pylons import app_globals
from datetime import datetime
from uuid import uuid1
from ftplib import FTP
from getmyad.lib.helpers import progressBar
from pylons import config
import getmyad.lib.helpers as h
import pymongo
import StringIO
import re
import getmyad


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
            yield {
                    'date': cost['date'],
                    'user_login': cost['user']['login'],
                    'cost': cost['cost']
                  }
        else:
            yield {
                    'date': None,
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
        
    
    def save(self):
        """ Сохраняет информер, при необходимости создаёт """
        update = {}
        if self.guid: update['guid'] = self.guid
        if self.title: update['title'] = self.title
        if self.admaker: update['admaker'] = self.admaker
        if self.css: update['css'] = self.css
        if self.user_login: update['user.login'] = self.user_login
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
        informer.write(""";document.write("<iframe src='http://rynok.yottos.com.ua/p_export.aspx?scr=%s' width='%s' height='%s'  frameborder='0' scrolling='no'></iframe>");""" 
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




class Account():
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
        
    
    def __init__(self, login):
        self.login = login
        self.email = ''
        self.password = ''
        self.phone = ''
        self.owner_name = ''
        self.min_out_sum = 100
        self.manager_get = None
        self.registration_date = datetime.now()
        
        self.db = Options.db 
        self.report = AccountReports(self)
        
        
    
    
    def register(self):
        ''' Регистрирует пользователя '''
        try:
            assert self.login, 'Login must be specified'
            assert self.db, 'Database connection must be assigned'
            self.db.users.ensure_index('login', unique=True)
            self.db.users.insert({'login': self.login,
    #                              'title': self.login,
                                  'password': self.password,
                                  'registrationDate': self.registration_date,
                                  'email': self.email,
                                  'phone': self.phone,
                                  'ownerName': self.owner_name,
                                  'minOutSum': self.min_out_sum,
                                  'managerGet': self.manager_get,
                                  'manager': False
                                  }, safe=True)
        except pymongo.errors.DuplicateKeyError:
            raise Account.AlreadyExistsError(self.login)


    def load(self):
        ''' Загружает аккаунт '''
        assert self.login, 'Login must be specified'
        
        record = self.db.users.find_one({'login': self.login})
        if not record:
            raise Account.NotFoundError(self.login)
        self.password = record['password']
        self.registration_date = record['registrationDate']
        self.email = record['email']
        self.phone = record['phone']
        self.owner_name = record['ownerName']
        self.min_out_sum = record['minOutSum']
        self.manager_get = record['managerGet']
            
    
    
    def domains(self):
        """ Возвращает список доменов, назначенных данному аккаунту """
        assert self.login, "Login not specifed!"
        data = db['user.domains'].find({'login': self.login})
        return [x['url'] for x in data if 'url' in x]
    
    
    def informers(self):
        """ Возвращает список информеров данного пользователя """
        result = []
        for object in db.Advertise.find({'user.login': self.login}):
            informer = Informer.load_from_mongo_record(object)
            result.append(informer)
        return result

    


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
