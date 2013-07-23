# encoding: utf-8
# This Python file uses the following encoding: utf-8
from celery.task import task, periodic_task
import ConfigParser
import datetime
import os
import socket
import pymongo
import xmlrpclib
import redis
import re

ADLOAD_XMLRPC_HOST = 'http://rpc-adload.yottos.com/rpc'
GETMYAD_XMLRPC_HOST = 'http://getmyad.yottos.com/rpc'
MONGO_HOST = '213.186.121.76:27018,213.186.121.199:27018,yottos.com'
MONGO_DATABASE = 'getmyad_db'
REDIS_LONG_HISTORY_HOST = 'localhost'
REDIS_LONG_HISTORY_PORT = 6382 
REDIS_CATEGORY_HOST = 'localhost'
REDIS_CATEGORY_PORT = 6384 

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


@task
def process_click(url, ip, click_datetime, offer_id, informer_id, token, server, valid, social, type, project,\
        isOnClick, branch, conformity, matching, title, country, city, referer, user_agent, cookie, view_seconds):
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

        ERROR ID LIST
        1 - Несовпадает Токен и IP
        2 - Найден в Чёрном списке IP
        3 - Более 3 переходов с РБ за сутки
        4 - Более 10 переходов с РБ за неделю
        5 - Более 5 переходов с ПС за сутки
        6 - Более 10 переходов с ПС за неделю
    '''
    print "/----------------------------------------------------------------------/"
    print "process click %s \t %s" % (ip, click_datetime)
    db = _mongo_main_db()
    REDIS_LONG_HISTORY_HOST = str(server)
    REDIS_CATEGORY_HOST = str(server)
    redis_long = redis.Redis(host = REDIS_LONG_HISTORY_HOST, port = REDIS_LONG_HISTORY_PORT, db = 0)
    redis_categor = redis.Redis(host = REDIS_CATEGORY_HOST, port = REDIS_CATEGORY_PORT, db = 0)
    
    def log_error(reason, campaign_id=None):
        db.clicks.error.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
                                'title': title, 'token': token, 'server': server,
                                'inf': informer_id, 'url': url, 'reason': reason,
                                'errorId': errorId, 'city': city, 'country': country,
                                'type': type, 'project': project, 'isOnClick': isOnClick,
                                'campaignId': campaign_id, 'referer':referer, 'user_agent':user_agent, 'cookie':cookie,
                                'view_seconds':view_seconds, 'campaignTitle': campaign_title},
                                safe=True)
    def log_reject(reason, campaign_id=None):
        db.clicks.rejected.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
                                   'title': title,  'token': token, 'server': server,
                                   'inf': informer_id, 'url': url, 'reason': reason,
                                   'errorId': errorId, 'city': city, 'country': country,
                                   'type': type, 'project': project, 'isOnClick': isOnClick,
                                   'campaignId': campaign_id, 'referer':referer, 'user_agent':user_agent, 'cookie':cookie,
                                   'view_seconds':view_seconds, 'campaignTitle': campaign_title},
                                   safe=True)


    def _partner_click_cost(informer_id, adload_cost):
        ''' Возвращает цену клика для сайта-партнёра.
            
            ``informer_id``
                ID информера, по которому произошёл клик.

            ``adload_cost``
                Цена клика для рекламодателя. Используется в случае плавающей
                цены.
        '''
        try:
            user = db.informer.find_one({'guid': informer_id}, ['user','cost'])
            if user.get('cost','None') == 'None':
                userCost = db.users.find_one({'login':user['user']}, {'cost':1, '_id':0})
                percent = int(userCost.get('cost',{}).get('ALL',{}).get('click',{}).get('percent',50))
                cost_min = float(userCost.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_min',  0.01))
                cost_max = float(userCost.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_max', 1.00))
                print "Account COST percent %s, cost_min %s, cost_max %s"% (percent, cost_min, cost_max)
            else:
                percent = int(user.get('cost',{}).get('ALL',{}).get('click',{}).get('percent',50))
                cost_min = float(user.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_min',  0.01))
                cost_max = float(user.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_max', 1.00))
                print "Informer COST percent %s, cost_min %s, cost_max %s"% (percent, cost_min, cost_max)

            cost = round(adload_cost * percent / 100, 2)
            if cost_min and cost < cost_min:
                cost = cost_min
            if cost_max and cost > cost_max:
                cost = cost_max
        except Exception as e :
            print e
            cost = 0
        return cost

    def _partner_blocked(informer_id):
        user_name = db.informer.find_one({'guid': informer_id}, ['user'])
        user = db.users.find_one({'login':user_name['user']})
        result = False
        block = user.get('blocked', False)
        if block:
            if block == 'banned':
                result = True
            elif block == 'light':
                result = True
            else:
                result = False
        return result
        
        
    

    # С тестовыми кликами ничего не делаем
    if token == "test":
        print "Processed test click from ip %s" % ip
        return
    # Определяем кампанию, к которой относится предложение
    try:
        of = db.offer.find_one({'guid': offer_id}, {'campaignId': True, 'campaignTitle': True, 'category':True, '_id': False})
        campaign_id = of.get('campaignId',None)
        campaign_title = of.get('campaignTitle',None)
        category = of.get('category',None)
    except (TypeError, KeyError):
        campaign_id = None
        campaign_title = None
        category = None

    try:
        c = re.compile(r'\W+', re.U)
        titler = c.sub(' ', title)
        if (cookie != None):
            redis_key = str(cookie + '-' + ip)
            redis_long.zadd(redis_key, titler.encode('utf-8'), 1)
            redis_categor.expire(redis_key,2592000)
            if (category != None and len(category) == 36):
                redis_categor.zadd(redis_key, category.encode('utf-8'), 1)
                redis_categor.expire(redis_key,2592000)
    except Exception as e:
        print e
    
    errorId = 0
    print "Token = %s" % token.encode('utf-8')
    print "Cookie = %s" % cookie
    print "IP = %s" % ip
    print "REFERER = %s" % referer.encode('utf-8')
    print "USER AGENT = %s" % user_agent.encode('utf-8')
    print "OfferId = %s" % offer_id.encode('utf-8')
    print "Offer Title = %s" % title.encode('utf-8')
    print "Informer = %s" % informer_id.encode('utf-8')
    print "Campaign Title = %s " % campaign_title.encode('utf-8')
    print "CampaignId = %s" % campaign_id.encode('utf-8')
    print "Project = %s" %  project.encode('utf-8')
    print "isOnClick = %s" % isOnClick
    print "User View-Click = %s" % view_seconds
    if not valid:
        errorId = 1
        log_reject(u'Не совпадает токен или ip')
        print "token ip false"
        print "rejected"
        return
    print "Geo = country %s, city %s " % (country.encode('utf-8'), city.encode('utf-8'))
    # Ищём IP в чёрном списке
    if db.blacklist.ip.find_one({'ip': ip, 'cookie': cookie}):
        errorId = 2
        print "Blacklisted ip:", ip, cookie
        log_reject("Blacklisted ip")
        return
    
    # Ищем, не было ли кликов по этому товару
    # Заодно проверяем ограничение на MAX_CLICKS_FOR_ONE_DAY переходов в сутки
    # (защита от накруток)
    MAX_CLICKS_FOR_ONE_DAY = 3
    MAX_CLICKS_FOR_ONE_DAY_ALL = 5
    MAX_CLICKS_FOR_ONE_WEEK = 10
    MAX_CLICKS_FOR_ONE_WEEK_ALL = 10
    unique = True
    #Проверяе по рекламному блоку за день и неделю
    today_clicks = 0
    toweek_clicks = 0
    for click in db.clicks.find({'ip': ip, 'cookie': cookie, 'inf': informer_id, 'dt': {'$lte': click_datetime, '$gte': (click_datetime - datetime.timedelta(weeks=1))}}).limit(MAX_CLICKS_FOR_ONE_DAY + MAX_CLICKS_FOR_ONE_WEEK):
        if (click_datetime - click['dt']).days == 0:
            today_clicks += 1
            toweek_clicks += 1
        else:
            toweek_clicks +=1

        if click['offer'] == offer_id:
            unique = False

    print "Total clicks for day in informers = %s" % today_clicks
    if today_clicks >= MAX_CLICKS_FOR_ONE_DAY:
        errorId = 3
        log_reject(u'Более %d переходов с РБ за сутки' % MAX_CLICKS_FOR_ONE_DAY)
        unique = False
        print 'Many Clicks for day to informer'
        db.blacklist.ip.update({'ip': ip, 'cookie': cookie},
                               {'$set': {'dt': datetime.datetime.now()}},
                               upsert=True)

    print "Total clicks for week in informers = %s" % toweek_clicks
    if toweek_clicks >= MAX_CLICKS_FOR_ONE_WEEK:
        errorId = 4
        log_reject(u'Более %d переходов с РБ за неделю' % MAX_CLICKS_FOR_ONE_WEEK)
        unique = False
        print 'Many Clicks for week to informer'
        db.blacklist.ip.update({'ip': ip, 'cookie':cookie},
                               {'$set': {'dt': datetime.datetime.now()}},
                               upsert=True)
    #Проверяе по ПС за день и неделю
    today_clicks_all = 0
    toweek_clicks_all = 0
    for click in db.clicks.find({'ip': ip, 'cookie': cookie, 'dt': {'$lte': click_datetime, '$gte': (click_datetime - datetime.timedelta(weeks=1))}}).limit(MAX_CLICKS_FOR_ONE_WEEK_ALL + MAX_CLICKS_FOR_ONE_DAY_ALL):
        if (click_datetime - click['dt']).days == 0:
            today_clicks_all += 1
            toweek_clicks_all += 1
        else:
            toweek_clicks_all +=1

        if click['offer'] == offer_id:
            unique = False

    print "Total clicks for day in all partners = %s" % today_clicks_all
    if today_clicks_all >= MAX_CLICKS_FOR_ONE_DAY_ALL:
        errorId = 5
        log_reject(u'Более %d переходов с ПС за сутки' % MAX_CLICKS_FOR_ONE_DAY_ALL)
        unique = False
        print 'Many Clicks for day to all partners'
        db.blacklist.ip.update({'ip': ip, 'cookie': cookie},
                               {'$set': {'dt': datetime.datetime.now()}},
                               upsert=True)

    print "Total clicks for week in all partners = %s" % toweek_clicks_all
    if toweek_clicks_all >= MAX_CLICKS_FOR_ONE_WEEK_ALL:
        errorId = 6
        log_reject(u'Более %d переходов с ПС за неделю' % MAX_CLICKS_FOR_ONE_WEEK_ALL)
        unique = False
        print 'Many Clicks for week to all partners'
        db.blacklist.ip.update({'ip': ip, 'cookie': cookie},
                               {'$set': {'dt': datetime.datetime.now()}},
                               upsert=True)
    if (_partner_blocked(informer_id)):
        print "Account block"
        return
        
    if project == 'adload':
        # Сохраняем клик в AdLoad
        adload_ok = True
        try:
            if unique:
                print "Adload RPC request"
                adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)
                adload_response = adload.addClick(offer_id, ip)
                adload_ok = adload_response.get('ok', False)
                print "Adload OK - %s" % adload_ok
                if not adload_ok and 'error' in adload_response:
                    log_error('Adload вернул ошибку: %s' %
                              adload_response['error'], campaign_id)
                adload_cost = adload_response.get('cost', 0)
                print "Adload COST %s" % adload_cost
        except Exception, ex:
            adload_ok = False
            log_error(u'Ошибка при обращении к adload: %s' % str(ex), campaign_id)
            print "adload failed"
        # Сохраняем клик в GetMyAd
        if not social and adload_ok:
            cost = _partner_click_cost(informer_id, adload_cost) if unique else 0
            db.clicks.insert({"ip": ip,
                              "city": city,
                              "country": country,
                              "offer": offer_id,
                              "campaignId": campaign_id,
                              "campaignTitle": campaign_title,
                              "title": title,
                              "dt": click_datetime,
                              "inf": informer_id,
                              "unique": unique,
                              "cost": cost,
                              "url": url,
                              "type": type,
                              "project": project,
                              "isOnClick": isOnClick,
                              "branch": branch,
                              "conformity": conformity,
                              "matching": matching,
                              "social":False,
                              "referer":referer,
                              "user_agent":user_agent,
                              "cookie":cookie,
                              "view_seconds":view_seconds},
                              safe=True)
            print "Payable click at the price of %s" % cost
        if social and adload_ok:
            cost = 0
            db.clicks.insert({"ip": ip,
                              "city": city,
                              "country": country,
                              "offer": offer_id,
                              "campaignId": campaign_id,
                              "campaignTitle": campaign_title,
                              "title": title,
                              "dt": click_datetime,
                              "inf": informer_id,
                              "unique": unique,
                              "cost": cost,
                              "url": url,
                              "type": type,
                              "project": project,
                              "isOnClick": isOnClick,
                              "branch": branch,
                              "conformity": conformity,
                              "matching": matching,
                              "social":True,
                              "referer":referer,
                              "user_agent":user_agent,
                              "cookie":cookie,
                              "view_seconds":view_seconds},
                              safe=True)
            print "Social click"
    elif project == 'banner':
        # Сохраняем клик в GetMyAd
        if not social:
            cost = 0
            db.clicks.insert({"ip": ip,
                              "city": city,
                              "country": country,
                              "offer": offer_id,
                              "campaignId": campaign_id,
                              "campaignTitle": campaign_title,
                              "title": title,
                              "dt": click_datetime,
                              "inf": informer_id,
                              "unique": unique,
                              "cost": cost,
                              "url": url,
                              "type": type,
                              "project": project,
                              "isOnClick": isOnClick,
                              "branch": branch,
                              "conformity": conformity,
                              "matching": matching,
                              "social":False,
                              "referer":referer,
                              "user_agent":user_agent,
                              "cookie":cookie,
                              "view_seconds":view_seconds},
                              safe=True)
            print "Payable click at the price of %s" % cost
        if social:
            cost = 0
            db.clicks.insert({"ip": ip,
                              "city": city,
                              "country": country,
                              "offer": offer_id,
                              "campaignId": campaign_id,
                              "campaignTitle": campaign_title,
                              "title": title,
                              "dt": click_datetime,
                              "inf": informer_id,
                              "unique": unique,
                              "cost": cost,
                              "url": url,
                              "type": type,
                              "project": project,
                              "isOnClick": isOnClick,
                              "branch": branch,
                              "conformity": conformity,
                              "matching": matching,
                              "social":True,
                              "referer":referer,
                              "user_agent":user_agent,
                              "cookie":cookie,
                              "view_seconds":view_seconds},
                              safe=True)
            print "Social click"
    elif project == 'cleverad':
        print "CleverAd Click"
    else:
        print "HZ"

    print "Click complite"
    print "/----------------------------------------------------------------------/"
