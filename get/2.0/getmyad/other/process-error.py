# encoding: utf-8
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
GETMYAD_XMLRPC_HOST = config.get('app:main', 'getmyad_xmlrpc_server')
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

def process_click(url, ip, click_datetime, offer_id, informer_id, token, server):
    ''' Обработка клика пользователя по рекламному предложению.

        Задача ставится в очередь скриптом redirect.py или выполняется
        немедленно при недоступности Celery.

        В процессе обработки:

        1. IP ищется в чёрном списке.

        2. Проверяется, что по ссылке переходит тот же ip, которому она была
           выдана.

        3. Проверяется, что ссылка ещё не устарела.

        4. Если ip сделал больше трёх переходов за сутки, ip заносится в чёрный
           список.

        5. Клик передаётся в AdLoad.

        6. Только если все предыдущие пункты отработали нормально, клик
           записывается в GetMyAd. В противном случае, делается запись либо
           в ``clicks.rejected`` (отклонённые клики), либо в ``clicks.error``
           (клики, во время обработки которых произошла ошибка).
    '''
    print "process click %s \t %s" % (ip, click_datetime)
    db = _mongo_main_db()
    title = ""
    
    def log_error(reason, campaign_id=None):
        print "error: ", reason 
#        db.clicks.error.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
#                                'title': title, 'token': token, 'server': server,
#                                'inf': informer_id, 'url': url, 'reason': reason,
#                                'campaignId': campaign_id},
#                                safe=True)
    def log_reject(reason, campaign_id=None):
        print 'reject:', reason
#        db.clicks.rejected.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
#                                   'title': title,  'token': token, 'server': server,
#                                   'inf': informer_id, 'url': url, 'reason': reason,
#                                   'campaignId': campaign_id},
#                                   safe=True)

    def _partner_click_cost(informer_id, adload_cost):
        ''' Возвращает цену клика для сайта-партнёра.
            
            ``informer_id``
                ID информера, по которому произошёл клик.

            ``adload_cost``
                Цена клика для рекламодателя. Используется в случае плавающей
                цены.
        '''
        try:
            user = db.informer.find_one({'guid': informer_id}, ['user'])['user']
            cursor = db.click_cost.find({'user.login': user,
                                         'date': {'$lte': click_datetime}}) \
                                  .sort('date', pymongo.DESCENDING) \
                                  .limit(1)
            x = cursor[0]
            payment_type = x.get('type', 'fixed') 
            if payment_type == 'floating':
                # Плавающая цена за клик
                percent = x['percent']
                cost_min = x.get('min')
                cost_max = x.get('max')
                cost = round(adload_cost * percent / 100, 2)
                if cost_min and cost < cost_min:
                    cost = cost_min
                if cost_max and cost > cost_max:
                    cost = cost_max
            else:
                # Фиксированная цена за клик
                payment_type = 'fixed'
                cost = float(x['cost'])
        except:
            cost = 0
        return cost
    

    # С тестовыми кликами ничего не делаем
    if token == "test":
        print "Processed test click from ip %s" % ip
        return
    
    # Ищём IP в чёрном списке
    if db.blacklist.ip.find_one({'ip': ip}):
        print "Blacklisted ip:", ip
        log_reject("Blacklisted ip")
        return
    
    social = (db.offer.find_one({'guid': offer_id}).get('campaignId') == 'e7e510fe-e3d4-4fdb-9a27-5e8cebbad057')
    
    if social:
        print "   social" 
    
    # Ищем, не было ли кликов по этому товару
    # Заодно проверяем ограничение на MAX_CLICKS_FOR_ONE_DAY переходов в сутки
    # (защита от накруток)
    MAX_CLICKS_FOR_ONE_DAY = 3
    today_clicks = 0
    unique = True
    for click in db.clicks.find({'ip': ip}) \
                   .sort("dt", pymongo.DESCENDING) \
                   .limit(MAX_CLICKS_FOR_ONE_DAY + 1):
        if (click_datetime - click['dt']).days == 0:
            today_clicks += 1
        if click['offer'] == offer_id:
            unique = False
    if today_clicks > MAX_CLICKS_FOR_ONE_DAY:
        log_reject(u'Более %d переходов за сутки' % MAX_CLICKS_FOR_ONE_DAY)
        unique = False
        db.blacklist.ip.ensure_index('ip')
        db.blacklist.ip.update({'ip': ip},
                               {'$set': {'dt': datetime.datetime.now()}},
                               upsert=True)

    # Определяем кампанию, к которой относится предложение
    try:
        campaign_id = db.offer.find_one({'guid': offer_id}, ['campaignId'])['campaignId']
    except (TypeError, KeyError):
        campaign_id = None
        
    # Сохраняем клик в AdLoad
    adload_ok = True
    try:
        if unique:
            adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)
            adload_response = adload.addClick(offer_id, ip)
            adload_ok = adload_response.get('ok', False)
            if not adload_ok and 'error' in adload_response:
                log_error('Adload вернул ошибку: %s' %
                          adload_response['error'], campaign_id)
            adload_cost = adload_response.get('cost', 0)
    except Exception, ex:
        adload_ok = False
        log_error(u'Ошибка при обращении к adload: %s' % str(ex), campaign_id)
        print "adload failed"

    # Сохраняем клик в GetMyAd
    if not social and adload_ok:
        cost = _partner_click_cost(informer_id, adload_cost) if unique else 0
        db.clicks.insert({"ip": ip,
                          "offer": offer_id,
                          "campaignId": campaign_id,
                          "title": title,
                          "dt": click_datetime,
                          "inf": informer_id,
                          "unique": unique,
                          "cost": cost,
                          "url": url},
                          safe=True)

if __name__ == '__main__':
    # TODO: Плавающая цена за клик
    raise NotImplementedError()

    db = pymongo.Connection(host='yottos.com').getmyad_db
    
    clicks = db.clicks.error.find({'dt': {'$gte': datetime.datetime(2011, 10, 13)}})
    for c in clicks:    
        try:
            process_click('url', c['ip'], c['dt'], c['offer'], c['inf'], c['token'], c['server'])
        except Exception as ex:
            print "Exception:", ex
