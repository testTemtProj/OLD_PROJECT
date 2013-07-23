# encoding: utf-8
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import pymongo.objectid

class MongoStats():
    def importImpressionsFromMongo(self, getmyad_worker_mongo_host, db):
        """ Импортирует статистику о показах из журнальной базы данных log_db_host/getmyad
		(для новой версии getmyad-worker)
		
		Возвращает структуру вида::
		
		    {
			count:        (кол-во обработанных записей),
			elapsed_time: (затраченное время, в секундах)
		    }
		
        """
        mongo = Connection(getmyad_worker_mongo_host)
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
        elapsed = (datetime.datetime.now() - elapsed_start_time).seconds
        print 'buffer has %s keys collected in %s seconds, %s records processed' % \
                (len(buffer), elapsed, processed_records)
        return {'count': processed_records,
		        'elapsed_time': (datetime.datetime.now() - elapsed_start_time).seconds}


	def importClicksFromMongo(self, db):
	    ''' Обработка кликов из mongo (новая версия getmyad-worker) '''
	    # _id последней записи, обработанной скриптом. Если не было обработано ничего, равно None
        elapsed_start_time = datetime.datetime.now()
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



	def processMongoStats(self, db):
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
	    
