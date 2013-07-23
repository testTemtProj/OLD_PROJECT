#!/usr/bin/python
# This Python file uses the following encoding: utf-8
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import bson.objectid
import hashlib

def importTrackingFromMongo(dbMain, dbLog):
    elapsed_start_time = datetime.datetime.now() 
    # _id последней записи, обработанной скриптом. Если не было обработано ничего, равно None 
    last_processed_id = None          
    try:
        last_processed_id = dbLog.log.config.find_one({'key': 'impressions last _id (2)'})['value']
    except:
        last_processed_id = None
    if not isinstance(last_processed_id, bson.objectid.ObjectId):
        last_processed_id = None

    cursor = dbLog['log.tracking'].find({}).sort("$natural", DESCENDING)
    try:
        end_id = cursor[0]['_id']   # Последний id, который будет обработан в этот раз
        print end_id
    except:
        print "importImpressionsFromMongo: nothing to do"
        return
    
    buffer = {}
    for x in cursor:
        if last_processed_id <> None and x['_id'] == last_processed_id:
            break
        key = (x.get('ip'), x.get('cookie'), x.get('cookie_tracking'), x.get('remarketing_url').lower())
        value = (x.get('dt'),x.get('search'),x.get('context'),x.get('account_id').lower())
        buffer[key] = value

    dbMain.reset_error_history()

    for key,value in buffer.items():
        dbMain.tracking.stats_daily.update({'ip': key[0],
                               'cookie': key[1],
                               'cookie_tracking': key[2]},
                               {'$set': {'remarketing_url.'+ hashlib.md5(str(key[3])).hexdigest(): [str(key[3]),value[1],value[2],value[3],value[0]], 'change': True}}, True)
    if dbMain.previous_error():
        print "Database error", dbMain.previous_error() 
    dbLog.log.config.update({'key': 'impressions last _id (2)'}, {'$set': {'value': end_id}}, True)


if __name__ == '__main__':
    print datetime.datetime.now()
    # Сервер основной базы данных, куда будет помещена обработанная статистика
    main_db_host = 'yottos.ru,213.186.121.76:27018,213.186.121.199:27018'

    # Адрес базы данных mongo, в которые пишет свои данные getmyad-worker
    getmyad_worker_mongo_host = 'localhost'


    connMain = Connection(host=main_db_host)
    dbMain = connMain.getmyad_db
    connLog = Connection(host=getmyad_worker_mongo_host)
    dbLog = connLog.getmyad_tracking
    
    importTrackingFromMongo(dbMain, dbLog)
