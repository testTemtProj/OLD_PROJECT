#!/usr/bin/python
# This Python file uses the following encoding: utf-8
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import pymongo.objectid

# Сервер основной базы данных, куда будет помещена обработанная статистика
main_db_host = '213.186.119.106:27017,213.186.121.201:27018,213.186.121.84:27018'

# Адрес базы данных mongo, в которые пишет свои данные getmyad-worker
getmyad_worker_mongo_host = 'localhost'


conn = Connection(host=main_db_host)
db = conn.getmyad_db

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
        db.offer.update({'guid': key[0]},
                        {'$inc': {'impressions': value}}, False)
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

        db.offer.update({'guid': x['offer']},
                        {'$inc':{'clicks': 1 if x['unique'] else 0}}, False)


    db.config.update({'key': 'clicks last _id (2)'}, {'$set': {'value': end_id}}, True)
    print "Finished in %s seconds" % (datetime.datetime.now() - elapsed_start_time).seconds 
    return {'count': processed_records,
            'elapsed_time': (datetime.datetime.now() - elapsed_start_time).seconds}


def rating_counting():
    date = datetime.date.today()
    date = datetime.datetime(date.year, date.month, date.day, 0, 0)
    old_count_impressions = db.stats_overall_by_date.find_one({'date': (date  - datetime.timedelta(days=7))},{"impressions":1 , '_id' : 0})
    coun_offers = db.offer.count()
    border_impressions = old_count_impressions['impressions'] / coun_offers
    offers = db.offer.find()
    for offer in offers:
        if offer.has_key('impressions'):
            impressions = offer['impressions']
            if offer.has_key('clicks'):
                clicks = offer['clicks']
            else:
                clicks = 0

            if impressions > border_impressions:
                #разобраться с ценой
                totalCost = 1.5
                rating = ((float(clicks)/impressions) * 100000) * totalCost
                db.offer.update({'guid': offer['guid']},{'$set': {'rating': round(rating, 4)}}, False)





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
    rating_counting()
    processMongoStats()
    
    # Делаем запись об обработке статистики
    mongo = pymongo.Connection(host=main_db_host)['getmyad_db']
    if 'log.statisticProcess' not in mongo.collection_names():
        mongo.create_collection('log.statisticProcess',
                                capped=True, size=50000000, max=10000)
    mongo.log.statisticProcess.insert({'dt': datetime.datetime.now(),
                                       'impressions': result_imps,
                                       'clicks': result_clicks,
                                       'srv': '1.2'},   
                                       safe=True)

    # Обновляем время обработки статистики
    mongo.config.update({'key': 'last stats_daily update date'},
                        {'$set': {'value': datetime.datetime.now()}}, safe=True)
