#!/usr/bin/python
# This Python file uses the following encoding: utf-8
from pymongo import Connection, DESCENDING
import datetime
import pymongo

# Сервер основной базы данных, куда будет помещена обработанная статистика
main_db_host = '213.186.119.106:27017,213.186.121.201:27018,213.186.121.84:27018'

# Адрес базы данных mongo, в которые пишет свои данные getmyad-worker
getmyad_worker_mongo_host = 'localhost'


conn = Connection(host=main_db_host)
db = conn.getmyad_db

userByAdvertise = {}            # Кеш {advertise_id => userLogin}


def processClick(ip, lot_guid, lot_title, dt, advertise_id):
    global userByAdvertise
    if not userByAdvertise:
        print "loading userByAdvertise"
        for x in db.informer.find():
            userByAdvertise[x['guid'].lower()] = x['user']
    
    lot_guid = lot_guid.lower()
    advertise_id = advertise_id.lower()
    
    lot = {"guid": lot_guid, "title": lot_title}
    ip_history = db.ip_history.find_one({"ip": ip})
    unique = True
    if ip_history:
        # Ищем, не было ли кликов по этому товару
        # Заодно проверяем ограничение на MAX_CLICKS_FOR_ONE_DAY переходов в сутки (защита от накруток)
        MAX_CLICKS_FOR_ONE_DAY = 3
        today_clicks = 0
        for click in ip_history['clicks']:
            if (datetime.datetime.today() - click['dt']).days == 0:
                today_clicks += 1
            if  click['lot'] == lot:
                unique = False
        if today_clicks >= MAX_CLICKS_FOR_ONE_DAY:
            db.clicks.rejected.insert({'ip': ip, 'lot': lot, 'dt': dt,
                                       'reason': u'Более 10 переходов за сутки'},
                                       safe=True)
            unique = False
    
    if unique:
        cursor = db.click_cost.find({'user.login': userByAdvertise.get(advertise_id.lower()),
                                     'date': {'$lte': dt}}).sort('date', DESCENDING).limit(1)
        try:
            cost = cursor[0]['cost']
        except:
            cost = 0   
    else:
        cost = 0


    db.log_clicks.insert({"ip": ip,
                          "lot": lot,
                          "dt": dt,
                          "adv": advertise_id,
                          "unique": unique,
                          "cost": cost})

    db.ip_history.update({"ip": ip}, 
                         {"$push": {"clicks": {"dt": dt, "lot": lot}}}, 
                          True)

    db.stats_daily.update({'lot.guid': lot_guid,
                           'lot.title': lot_title,
                           'adv': advertise_id,
                           'date': datetime.datetime.fromordinal(dt.toordinal())},
                           {'$inc': {'clicks': 1,
                                     'clicksUnique': 1 if unique else 0,
                                     'totalCost': cost if unique else 0}
                           },
                           True)



def importImpressionsFromMongo(log_db_host):
    """ Импортирует статистику о показах из журнальной базы данных log_db_host/getmyad
        (для новой версии getmyad-worker)
        
        Возвращает структуру вида::
        
            {
                count:        (кол-во обработанных записей),
                elapsed_time: (затраченное время, в секундах)
            }
        
         """
    global db                   # База данных со статистикой
    mongo = Connection(log_db_host)
    db2 = mongo.getmyad         # База данных с журналом показов
    
    # _id последней записи, обработанной скриптом. Если не было обработано ничего, равно None 
    last_processed_id = None          
    try:
        last_processed_id = db2.config.find_one({'key': 'impressions last _id (2)'})['value']
    except:
        last_processed_id = None
    if not isinstance(last_processed_id, pymongo.objectid.ObjectId):
        last_processed_id = None

    cursor = db2['log.impressions'].find().sort("$natural", DESCENDING)
    try:
        end_id = cursor[0]['_id']   # Последний id, который будет обработан в этот раз
    except:
        print "importImpressionsFromMongo: nothing to do"
        return
    
    buffer = {}
    elapsed_start_time = datetime.datetime.now()
    processed_records = 0
    for x in cursor:
        if last_processed_id <> None and x['_id'] == last_processed_id:
            break
        if x.get('social', False):
            continue
        n = x['dt']
        dt = datetime.datetime(n.year, n.month, n.day)
        key = (x['id'], x['title'], x['inf'].lower(), dt)
        buffer[key] = buffer.get(key, 0) + 1
        processed_records += 1
    elapsed = (datetime.datetime.now() - elapsed_start_time).seconds
    print 'buffer has %s keys collected in %s seconds, %s records processed' % \
            (len(buffer), elapsed, processed_records)

    db.reset_error_history()
    for key,value in buffer.items():
        db.stats_daily.update({'lot.guid': key[0],
                               'lot.title': key[1],
                               'adv': key[2],
                               'date': key[3]},
                               {'$inc': {'impressions': value}},
                               True)
    if db.previous_error():
        print "Database error", db.previous_error() 
    db2.config.update({'key': 'impressions last _id (2)'}, {'$set': {'value': end_id}}, True)
    return {'count': processed_records,
            'elapsed_time': (datetime.datetime.now() - elapsed_start_time).seconds}


def importClicksFromMongo():
    ''' Обработка кликов из mongo (новая версия getmyad-worker) '''
    global db
    # _id последней записи, обработанной скриптом. Если не было обработано ничего, равно None 
    last_processed_id = None          
    try:
        last_processed_id = db.config.find_one({'key': 'clicks last _id (2)'})['value']
    except:
        last_processed_id = None
    if not isinstance(last_processed_id, pymongo.objectid.ObjectId):
        last_processed_id = None

    cursor = db['clicks'].find().sort("$natural", DESCENDING)
    try:
        end_id = cursor[0]['_id']   # Последний id, который будет обработан в этот раз
    except:
        print "importClicksFromMongo: nothing to do"
        return
    
    buffer = {}
    elapsed_start_time = datetime.datetime.now()
    processed_records = 0
    for x in cursor:
        if last_processed_id <> None and x['_id'] == last_processed_id:
            break
        processed_records += 1
        db.stats_daily.update({'lot.guid': x['offer'],
                               'lot.title': x['title'],
                               'adv': x['inf'],
                               'date': datetime.datetime.fromordinal(x['dt'].toordinal())},
                               {'$inc': {'clicks': 1,
                                         'clicksUnique': 1 if x['unique'] else 0,
                                         'totalCost': x['cost']}}, True)
    db.config.update({'key': 'clicks last _id (2)'}, {'$set': {'value': end_id}}, True)
    print "Finished in %s seconds" % (datetime.datetime.now() - elapsed_start_time).seconds 
    return {'count': processed_records,
            'elapsed_time': (datetime.datetime.now() - elapsed_start_time).seconds}



def processMongoStats():
    """ Обновляет промежуточную статистику в mongo"""
    db.eval('''
        function() {
            var startDate = new Date();
            startDate.setDate((new Date).getDate() - 2);
            
            var a = db.stats_daily.group({
                    key: {adv:true, date:true},
                    cond: {date: {$gt: startDate}},
                    reduce: function(obj,prev){
                                                prev.totalCost += obj.totalCost || 0;
                                                prev.impressions += obj.impressions || 0;
                                                prev.clicks += obj.clicks || 0;
                                                prev.clicksUnique += obj.clicksUnique || 0;
                                            },
                    initial: {totalCost: 0,
                              impressions:0,
                              clicks:0,
                              clicksUnique:0}})
                              
            for (var i=0; i<a.length; i++) {
                var o = a[i];
                db.stats_daily_adv.update(
                    {adv: o.adv, date: o.date},
                    {$set: {totalCost: o.totalCost,
                            impressions: o.impressions,
                            clicks: o.clicks,
                            clicksUnique: o.clicksUnique,
                            totalCost: o.totalCost
                            }},
                    {upsert: true})
            }
            
            db.stats_daily_adv.ensureIndex({adv:1})
        }
        ''')
    


if __name__ == '__main__':
    result_imps = importImpressionsFromMongo(getmyad_worker_mongo_host)
    result_clicks = importClicksFromMongo()
    processMongoStats()
    
    # Делаем запись об обработке статистики
    mongo = pymongo.Connection(host=main_db_host)['getmyad_db']
    if 'log.statisticProcess' not in mongo.collection_names():
        mongo.create_collection('log.statisticProcess',
                                capped=True, size=50000000, max=10000)
    mongo.log.statisticProcess.insert({'dt': datetime.datetime.now(),
                                       'impressions': result_imps,
                                       'clicks': result_clicks},
                                       safe=True)
