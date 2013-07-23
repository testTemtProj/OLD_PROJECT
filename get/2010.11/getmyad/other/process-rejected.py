# encoding: utf-8

from celery.decorators import task, periodic_task
from datetime import datetime
from getmyad.tasks import tasks
import ConfigParser
import datetime
import os
import pymongo
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


def process_click(url, ip, click_datetime, offer_id, informer_id, token, server):
    ''' Обработка перехода по ссылке ``url`` '''
    print "process click: %s\t%s" % (ip, click_datetime)
    try:
        mongo_connection = pymongo.Connection(host=MONGO_HOST)
        db = mongo_connection[MONGO_DATABASE]
    except pymongo.errors.AutoReconnect, ex:
        print str(ex)
        return
    title = ""
    
    def log_error(reason):
        print "error: ", reason
#        db.clicks.error.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
#                                'title': title, 'token': token, 'server': server,
#                                'inf': informer_id, 'reason': reason},
#                                safe=True)
    def log_reject(reason):
        print 'reject:', reason
#        db.clicks.rejected.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
#                                   'title': title,  'token': token, 'server': server,
#                                   'inf': informer_id, 'reason': reason},
#                                   safe=True)
    
    # С тестовыми кликами ничего не делаем
    if token == "test":
        print "Processed test click from ip %s" % ip
        return
    
    # Ищём IP в чёрном списке
    if db.blacklist.ip.find_one({'ip': ip}):
        log_reject("Blacklisted ip")
        return
    
    valid = True
    social = (db.offer.find_one({'guid': offer_id}).get('campaignId') == 'e7e510fe-e3d4-4fdb-9a27-5e8cebbad057')
    if social:
        print "   social" 
    
    if not valid:
        log_reject(u'Не совпадает токен или ip')
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




if __name__ == '__main__':
    db = pymongo.Connection(host='yottos.com').getmyad_db
    clicks = db.clicks.rejected.find({'dt': {'$gte': datetime.datetime(2010, 8, 26, 17, 50)}})
    for c in clicks:
        if c['reason'] == u'Не совпадает токен или ip':
            try:
                process_click('url', c['ip'], c['dt'], c['offer'], c['inf'], c['token'], c['server'])
            except Exception as ex:
                print "Exception:", ex

