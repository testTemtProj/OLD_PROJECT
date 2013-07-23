# encoding: utf-8
from celery.decorators import task, periodic_task
import ConfigParser
import datetime
import os
import socket
import pymongo
import pymongo.objectid
import xmlrpclib
from statistic import MongoStats

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
getmyad_worker_mongo_host = 'localhost'


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
        db.clicks.error.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
                                'title': title, 'token': token, 'server': server,
                                'inf': informer_id, 'url': url, 'reason': reason,
                                'campaignId': campaign_id},
                                safe=True)
    def log_reject(reason, campaign_id=None):
        db.clicks.rejected.insert({'ip': ip, 'offer': offer_id, 'dt': click_datetime,
                                   'title': title,  'token': token, 'server': server,
                                   'inf': informer_id, 'url': url, 'reason': reason,
                                   'campaignId': campaign_id},
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
    if today_clicks >= MAX_CLICKS_FOR_ONE_DAY:
        log_reject(u'Более %d переходов за сутки' % MAX_CLICKS_FOR_ONE_DAY)
        unique = False
        db.blacklist.ip.ensure_index('ip')
        db.blacklist.ip.update({'ip': ip},
                               {'$set': {'dt': datetime.datetime.now()}},
                               upsert=True)

    # Определяем кампанию, к которой относится предложение
    try:
        campaign_id = \
            db.offer.find_one({'guid': offer_id}, ['campaignId'])['campaignId']
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


@periodic_task(run_every=datetime.timedelta(days=1))
def clean_ip_blacklist():
    ''' Удаляет старые записи из чёрного списка '''
    db = _mongo_main_db()
    db.blacklist.ip.remove({'dt': {'$lte': datetime.datetime.now() - datetime.timedelta(weeks=4)}})
    print "Blacklist cleaned!"


@periodic_task(run_every=datetime.timedelta(hours=8))
def decline_unconfirmed_moneyout_requests():
    ''' Отклоняет заявки, которые пользователи не подтвердили в течении трёх
        дней '''
    print "decline_unconfirmed_moneyout_requests()"
    db = _mongo_main_db()
    clean_to_date = datetime.datetime.now() - datetime.timedelta(days=3)
    db.money_out_request.remove(
                    {'user_confirmed': {'$ne' : True},
                     'approved': {'$ne': True},
                     'date': {'$lte': clean_to_date}}, safe=True)


@periodic_task(run_every=datetime.timedelta(minutes=30))
def agregate_stats():
    ''' Обработка (агрегация) статистики '''
    print "agregate_stats is starting"
    db = _mongo_main_db()

    def _count_AccountsDomains_overall_by_date(date):
        ''' Просчитывает кол-во активных аккаунтов и сайтов по предприятию с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date.  '''
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        act_acc_count = 0
        yest_act_acc_count = 0
        b_yest_act_acc_count = 0
        domains_yday = 0
        domains_byday = 0
        domains_today = 0
        users = [x['login'] for x in db.users.find({'accountType': 'user'}).sort('registrationDate')]
        for x in db.user.summary_per_date.find():
            '''TODO Почистить базу от Сивоконь вей и убрать эту дуратскую проверку на вхождения пользователя'''
            if x['login'] not in users: continue
            if x['activity'] == 'greenflag':
                act_acc_count += 1 
            if x['activity_yesterday'] == 'greenflag':
                yest_act_acc_count += 1
            if x['activity_before_yesterday'] == 'greenflag':
                b_yest_act_acc_count += 1
            active_domains = x.get('active_domains', {})
            domains_today += active_domains.get('today', 0)
            domains_yday += active_domains.get('yesterday', 0)
            domains_byday += active_domains.get('before_yesterday', 0)
        print act_acc_count
        print yest_act_acc_count
        print b_yest_act_acc_count
        print domains_yday
        print domains_byday
        print domains_today
        db.stats_overall_by_date.update({'date': date },
                                        {'$set': {'act_acc_count': act_acc_count,
                                                  'domains_today': domains_today}},
                                        upsert=True)
    
    def _agregate_overall_by_date(date):
        ''' Составляет общую статистику по предприятию с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
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
    _count_AccountsDomains_overall_by_date(datetime.date.today())                   # Считаем количество активных аккаунтов и сайтов за сегодня
    _agregate_overall_by_date(datetime.date.today() - datetime.timedelta(days=1))   # За вчера
    print "Stats agregated."


@periodic_task(run_every=datetime.timedelta(days=1))
def archive_old_stats():
    ''' Помещает старую статистику в архив. '''
    print "arhive_old_data started"
    db = _mongo_main_db()
    archive = _mongo_connection()['getmyad_archive']
    archive_to_date = datetime.datetime.now() - datetime.timedelta(days=60)
    i = 0
    for x in db.stats_daily.find({'date': {'$lt': archive_to_date}}):
        archive.stats_daily.save(x)
        db.stats_daily.remove(x)
        i += 1
    print "%d records moved to archive" % i
        
        

@periodic_task(run_every=datetime.timedelta(minutes=10))
def check_outdated_campaigns():
    ''' Иногда AdLoad не оповещает GetMyAd об остановке кампании, об отработке
        парсера и т.д. Это приводит к тому, что кампания продолжает крутиться
        в GetMyAd, но клики не засчитываются и записываются в clicks.error.
        Данная задача проверяет, не произошло ли за последнее время несколько
        таких ошибок и, если произошло, обновляет кампанию. '''

    WATCH_LAST_N_MINUTES = 30   # Смотрим лог за последние N минут
    ALLOWED_ERRORS = 0          # Допустимое количество ошибок на одну кампанию

    # Смотрим лог ошибок, начиная с конца
    db = _mongo_main_db()
    c = db['clicks.error'].find().sort('$natural', pymongo.DESCENDING)
    now = datetime.datetime.now()
    errors_per_campaign = {}
    for item in c:
        if (now - item['dt']).seconds > 15 * 60:
            break
        campaign = item.get('campaignId')
        errors_per_campaign.setdefault(campaign, 0)
        errors_per_campaign[campaign] += 1

    # Обновляем кампании, у которых превышен лимит ошибок
    outdated_campaigns = [c for c, e in errors_per_campaign.items()
                                     if e > ALLOWED_ERRORS]
    if outdated_campaigns:
        print "outdated_campaigns = %s" % repr(outdated_campaigns)
    else:
        print "No outdated campaigns"
    for campaign in outdated_campaigns:
        if campaign is None:
            print "Unknown campaign, skipped"
            continue
        rpc = xmlrpclib.ServerProxy(GETMYAD_XMLRPC_HOST)
        rpc.campaign.update(campaign)

#@periodic_task(run_every=datetime.timedelta(minutes=30))
def stats_daily_update_impressions():
    print "Обновляет статистику показов в stats_daily"
    db = _mongo_main_db()
    result_imps = MongoStats().importImpressionsFromMongo(getmyad_worker_mongo_host , db)
    # Делаем запись об обработке статистики
    if 'log.statisticProcess' not in db.collection_names():
        db.create_collection('log.statisticProcess',
                                capped=True, size=50000000, max=10000)
    db.log.statisticProcess.insert({'dt': datetime.datetime.now(),
                                       'impressions': result_imps,
                                       'srv': socket.gethostname()},
                                       safe=True)

    # Обновляем время обработки статистики
    print "Обновляем время обработки статистики"
    print datetime.datetime.now()
    db.config.update({'key': 'last stats_daily update date'},
                        {'$set': {'value': datetime.datetime.now()}}, safe=True)

#@periodic_task(run_every=datetime.timedelta(minutes=30))
def stats_daily_update_clicks():
    print "Обновляет статистику кликов в stats_daily"
    db = _mongo_main_db()
    result_clicks = MongoStats().importClicksFromMongo(db)
    if 'log.statisticProcess' not in db.collection_names():
        db.create_collection('log.statisticProcess',
                                capped=True, size=50000000, max=10000)
    db.log.statisticProcess.insert({'dt': datetime.datetime.now(),
                                       'clicks': result_clicks,
                                       'srv': socket.gethostname()},
                                       safe=True)
    # Обновляем время обработки статистики
    print "Обновляем время обработки статистики"
    print datetime.datetime.now()
    db.config.update({'key': 'last stats_daily update date'},
                       {'$set': {'value': datetime.datetime.now()}}, safe=True)

#@periodic_task(run_every=datetime.timedelta(minutes=35))
def stats_daily_adv_update():
    elapsed_start_time = datetime.datetime.now()
    print "Обновляет промежуточную статистику в stats_daily_adv"
    db = _mongo_main_db()
    MongoStats().processMongoStats(db)
    print '''Обновление промежуточной статистики в stats_daily_adv произошло за %s секунд''' % (datetime.datetime.now() - elapsed_start_time).seconds
    # Обновляем время обработки статистики
    print "Обновляем время обработки статистики"
    print datetime.datetime.now()
    db.config.update({'key': 'last stats_daily update date'},
                     {'$set': {'value': datetime.datetime.now()}}, safe=True)

