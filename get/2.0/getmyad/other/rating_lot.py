#!/usr/bin/python
# This Python file uses the following encoding: utf-8
#Устаревшее не используеться, чисто для примеров оставлено
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import xmlrpclib



adload = xmlrpclib.ServerProxy('http://adload.vsrv-1.2.yottos.com/rpc')

# Сервер основной базы данных, куда будет помещена обработанная статистика
#main_db_host = '213.186.119.106:27017,213.186.121.201:27018,213.186.121.84:27018'


conn = Connection(host=main_db_host)
db = conn.getmyad_db

def processMongoStats():
    reduce = 'function(obj,prev){prev.impressions += obj.impressions || 0; prev.clicksUnique += obj.clicksUnique || 0;}'
    initial = {'impressions':0, 'clicksUnique':0}
#    startDate = datetime.datetime.now()
    try:
        start = db.config.find_one({'key': 'lot_last_agregate_date'})['value']
    except:
        start = datetime.datetime.now()
#    start = datetime.datetime(2011, 11, 16)
    cursor = db.stats_daily_lot.find().sort("$natural", DESCENDING)
    end = cursor[0]['date']
    type(end)
    db.config.update({'key': 'lot_last_agregate_date'}, {'$set': {'value': end}}, True)
    date = datetime.date.today()
    date = datetime.datetime(date.year, date.month, date.day, 0, 0)
    old_count_impressions = db.stats_overall_by_date.find_one({'date': (date  - datetime.timedelta(days=7))},{"impressions":1 , '_id' : 0}) 
    coun_offer = db.offer.count()
    border_impressions = old_count_impressions['impressions'] / coun_offer
    a = db.stats_daily_lot.group(key={'guid':True},condition={'date':{'$gt': start, '$lte': end}},initial=initial,reduce=reduce)
    #a = []
    for item in a:
        offer = db.offer.find_one({'guid': item['guid']})
        if  offer != None:
            if offer.has_key('impressions'):
                impressions = offer['impressions'] + item['impressions']
            else:
                impressions = item['impressions']

            if offer.has_key('clicksUnique'):
                clicksUnique = offer['clicksUnique'] + item['clicksUnique']
            else:
                clicksUnique = item['clicksUnique']


            if impressions > border_impressions:
                #разобраться с ценой 
                totalCost = 1.5 
                rating = ((clicksUnique/impressions) * 100000) * totalCost
                print round(rating, 4)
                db.offer.update({'guid': item['guid']},{'$set': {'impressions': impressions, 'clicksUnique': clicksUnique, 'totalCost': totalCost, 'rating': round(rating, 4)}}, upsert=True)
            else:
                db.offer.update({'guid': item['guid']},{'$set': {'impressions': impressions, 'clicksUnique': clicksUnique}}, upsert=True)
        else:
            print "Не найдено рекламное предложение"



if __name__ == '__main__':
    processMongoStats()
