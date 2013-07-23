# encoding: utf-8
from celery.decorators import task, periodic_task
import ConfigParser
import datetime
import os
import pymongo
import xmlrpclib

PYLONS_CONFIG = "deploy.ini"
#PYLONS_CONFIG = "development.ini"

config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config = ConfigParser.ConfigParser()
config.read(config_file)

ADLOAD_XMLRPC_HOST = config.get('app:main', 'adload_xmlrpc_server')
MONGO_HOST = config.get('app:main', 'mongo_host')
MONGO_USER = config.get('app:main', 'mongo_user')
MONGO_PASSWORD = config.get('app:main', 'mongo_password')
MONGO_DATABASE = config.get('app:main', 'mongo_database')

def _connect_to_mongo():
    ''' Возвращает подключение к базе данных MongoDB '''
    try:
        mongo_connection = pymongo.Connection(host=MONGO_HOST)
    except pymongo.errors.AutoReconnect:
        # Пауза и повторная попытка подключиться
        from time import sleep
        sleep(1)
        mongo_connection = pymongo.Connection(host=MONGO_HOST)
    db = mongo_connection[MONGO_DATABASE]
    return db

@task
def process_click(url, ip, click_datetime, offer_id, informer_id, token, server):
    ''' Обработка перехода по ссылке ``url`` '''
    print "process click %s \t %s" % (ip, click_datetime)
    db = _connect_to_mongo()
    title = ""
    
    def log_error(reason):
        db.clicks.error.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
                                'title': title, 'token': token, 'server': server,
                                'inf': informer_id, 'reason': reason},
                                safe=True)
    def log_reject(reason):
        db.clicks.rejected.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
                                   'title': title,  'token': token, 'server': server,
                                   'inf': informer_id, 'reason': reason},
                                   safe=True)
    
    # С тестовыми кликами ничего не делаем
    if token == "test":
        print "Processed test click from ip %s" % ip
        return
    
    # Ищём IP в чёрном списке
    if db.blacklist.ip.find_one({'ip': ip}):
        print "Blacklisted ip:", ip
        log_reject("Blacklisted ip")
        return
    
    # Проверяем действительность токена
    valid = False
    try:
        mongo_log = pymongo.Connection(host=server).getmyad
    except pymongo.errors.AutoReconnect:
        log_error(u'Не могу подключиться к серверу %s' % server)
        return
    for x in mongo_log.log.impressions.find({'token': token}):
        if x['ip'] == ip and x['id'] == offer_id:
            valid = True
            title = x['title']
            social = x.get('social', False)
            break
        
    if not valid:
        log_reject(u'Не совпадает токен или ip')
        print "rejected"
        return
    
    # Ищем, не было ли кликов по этому товару
    # Заодно проверяем ограничение на MAX_CLICKS_FOR_ONE_DAY переходов в сутки (защита от накруток)
    MAX_CLICKS_FOR_ONE_DAY = 3
    today_clicks = 0
    unique = True
    for click in db.clicks.find({'ip': ip}).sort("$natural", pymongo.DESCENDING).limit(MAX_CLICKS_FOR_ONE_DAY + 1):
        if (click_datetime - click['dt']).days == 0:
            today_clicks += 1
        if click['offer'] == offer_id:
            unique = False
    if today_clicks > MAX_CLICKS_FOR_ONE_DAY:
        log_reject(u'Более %d переходов за сутки' % MAX_CLICKS_FOR_ONE_DAY)
        unique = False
        db.blacklist.ip.ensure_index('ip')
        db.blacklist.ip.update({'ip': ip}, {'$set': {'dt': datetime.datetime.now()}}, upsert=True)

    # Определяем цену клика для сайта-партнёра 
    if unique:
        try:
            user = db.informer.find_one({'guid': informer_id}, ['user'])['user']
            cursor = db.click_cost.find({'user.login': user,
                                         'date': {'$lte': click_datetime}}).sort('date', pymongo.DESCENDING).limit(1)
            cost = float(cursor[0]['cost'])
        except:
            cost = 0   
    else:
        cost = 0
        
    # Сохраняем клик в AdLoad
    adload_ok = True
    try:
        if unique:
            adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)
            adload_response = adload.addClick(offer_id, ip)
            adload_ok = adload_response.get('ok', False)
            if not adload_ok and 'error' in adload_response:
                log_error('Adload вернул ошибку: %s' % adload_response['error'])
    except Exception, ex:
        adload_ok = False
        log_error(u'Ошибка при обращении к adload: %s' % str(ex))
        print "adload failed"

    # Сохраняем клик в GetMyAd
    if not social and adload_ok:
        db.clicks.insert({"ip": ip,
                          "offer": offer_id,
                          "title": title,
                          "dt": click_datetime,
                          "inf": informer_id,
                          "unique": unique,
                          "cost": cost},
                          safe=True)


@periodic_task(run_every=datetime.timedelta(days=1))
def clean_ip_blacklist():
    ''' Удаляет старые записи из чёрного списка '''
    db = _connect_to_mongo()
    db.blacklist.ip.remove({'dt': {'$lte': datetime.datetime.now() - datetime.timedelta(weeks=4)}})
    print "Blacklist cleaned!"


@periodic_task(run_every=datetime.timedelta(minutes=30))
def agregate_stats():
    ''' Обработка (агрегация) статистики '''
    db = _connect_to_mongo()
    
    def _agregate_overall_by_date(date):
        ''' Составляет общую статистику по предприятию с разбивкой по датам.
            
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date.  '''
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        
        summary = db.stats_daily_adv.group(
            key = ['date'],
            condition = {'date': {'$gte': date,
                                  '$lt': date + datetime.timedelta(days=1)}},
            reduce = '''
                function(o, p) {
                   p.clicks += o.clicks || 0;
                   p.clicksUnique += o.clicksUnique || 0;
                   p.impressions += o.impressions || 0;
                   p.totalCost += o.totalCost || 0;
                }''',
            initial = {'clicks': 0, 'clicksUnique': 0, 'impressions': 0, 'totalCost': 0}
        )
        for x in summary:
            db.stats_overall_by_date.update({'date': x['date']},
                                            {'$set': {'clicks': x['clicks'],
                                                      'clicksUnique': x['clicksUnique'],
                                                      'impressions': x['impressions'],
                                                      'totalCost': x['totalCost']}},
                                            upsert=True)
    _agregate_overall_by_date(datetime.date.today())                                # За сегодня
    _agregate_overall_by_date(datetime.date.today() - datetime.timedelta(days=1))   # За вчера
    print "Stats agregated."
    