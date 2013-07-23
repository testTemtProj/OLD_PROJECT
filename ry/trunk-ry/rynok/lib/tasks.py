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

def _mongo_connection():
    ''' Возвращает Connection к серверу MongoDB '''
    try:
        connection = pymongo.Connection(host=MONGO_HOST)
    except pymongo.errors.AutoReconnect:
        # Пауза и повторная попытка подключиться
        from time import sleep
        sleep(1)
        connection = pymongo.Connection(host=MONGO_HOST)
    return connection

def _mongo_main_db():
    ''' Возвращает подключение к базе данных MongoDB '''
    return _mongo_connection()[MONGO_DATABASE]


@task(ignore_result=True)
def process_click(params):
    ''' Обработка перехода по ссылке ``url`` '''

    ip = params.get('ip')
    dt = params.get('dt')
    url = params.get('url', 'None')
    offerId = params.get('offerId', 'None')
    shopId = params.get('shopId', 'None')
    vendor = params.get('vendor', 'None')
    campaignId = params.get('campaign_id', None)
    title = params.get('title', 'None')
    

    def log_error(reason, campaignId=None):
        db.clicks.error.insert({'ip': ip, 'offer': offerId, 'dt': dt,
                                'title': title, 'shop': shopId, 'url': url, 'reason': reason,
                                'campaignId': campaignId},
                                safe=True)
    def log_reject(reason, campaignId=None):
        db.clicks.rejected.insert({'ip': ip, 'offer': offerId, 'dt': dt,
                                   'title': title, 'url': url, 'reason': reason,
                                   'campaignId': campaignId},
                                   safe=True)
        
    print "process click %s \t %s" % (ip, dt)
    db = _mongo_main_db()
      
    # Ищём IP в чёрном списке
    if db.blacklist.ip.find_one({ip: ip}):
        print "Blacklisted ip:", ip
        log_reject("Blacklisted ip")
        return
       
    # Ищем, не было ли кликов по этому товару
    # Заодно проверяем ограничение на MAX_CLICKS_FOR_ONE_DAY переходов в сутки (защита от накруток)
    MAX_CLICKS_FOR_ONE_DAY = 2
    today_clicks = 0
    unique = True

    #TODO сделать через group
    for click in db.clicks.find({'ip': ip}).sort("dt", pymongo.DESCENDING).limit(MAX_CLICKS_FOR_ONE_DAY + 1):
        if (dt - click['dt']).days == 0:
            today_clicks += 1
        if click['offer'] == offerId:
            unique = False

    if today_clicks > MAX_CLICKS_FOR_ONE_DAY:
        log_reject(u'Более %d переходов за сутки' % MAX_CLICKS_FOR_ONE_DAY)
        unique = False
        db.blacklist.ip.ensure_index('ip')
        db.blacklist.ip.update({'ip': ip}, {'$set': {'dt': datetime.datetime.now()}}, upsert=True)

    # Определяем кампанию, к которой относится предложение
    if campaignId is None:
        print "Случилось что-то плохое с campaignId в process_click() tasks.py"
	log_error("Случилось что-то плохое с campaignId в process_click() tasks.py")
        return

    # Сохраняем клик в AdLoad
    adload_ok = True
    try:
        if unique:
            adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)            
            adload_response = adload.addClick(campaignId, str(offerId), shopId, ip, title)
            adload_ok = adload_response.get('ok', False)
            print adload_response
            if not adload_ok and 'error' in adload_response:                
                log_error('Adload вернул ошибку: %s' % adload_response['error'])
    except Exception, ex:
        adload_ok = False
        log_error(u'Ошибка при обращении к adload: %s' % str(ex))
        print "adload failed"

    # Сохраняем клик в базу статистики
    social = False
    print "Insert in db"
    if not social and adload_ok:
        db.clicks.insert({"ip": ip,
                          "offer": offerId,
                          "campaignId": campaignId,
                          "title": title,
                          "shopId":shopId,
                          "vendor":vendor,
                          "dt": dt,                                                    
                          "url": url},
                          safe=True)


@periodic_task(run_every=datetime.timedelta(days=1))
def clean_ip_blacklist():
    ''' Удаляет старые записи из чёрного списка '''
    db = _mongo_main_db()
    db.blacklist.ip.remove({'dt': {'$lte': datetime.datetime.now() - datetime.timedelta(weeks=4)}})
    print "Blacklist cleaned!"
