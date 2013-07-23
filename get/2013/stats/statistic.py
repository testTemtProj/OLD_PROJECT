# encoding: utf-8
from pymongo import Connection, DESCENDING
import logging, logging.handlers, sys, os 
import datetime
import pymongo
import bson.objectid
import socket
from mq import MQ
from pprint import pprint
import xlwt
import StringIO
import ftplib


class GetmyadStats(object):


    def importBadClicksFromMongo(self, db):
        u"""Обработка отклоненных кликов из mongo"""
        date = datetime.datetime.now()
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        bufblacklistIp = {}
        bufbadTokenIp = {}
        bufmanyClicks = {}
        for clicks in db.clicks.rejected.find({'dt': {'$gte': date} }):
            error = clicks.get('errorId', None)
            if error == 1:
                n = clicks['dt']
                dt = datetime.datetime(n.year, n.month, n.day)
                key = (clicks['offer'], clicks['inf'].lower(), dt, clicks['country'], clicks['city'], clicks['campaignId'], clicks.get('isOnClick', True))
                bufbadTokenIp[key] = bufbadTokenIp.get(key, 0) + 1

            elif error == 2:
                n = clicks['dt']
                dt = datetime.datetime(n.year, n.month, n.day)
                key = (clicks['offer'], clicks['inf'].lower(), dt, clicks['country'], clicks['city'], clicks['campaignId'], clicks.get('isOnClick', True))
                bufblacklistIp[key] = bufblacklistIp.get(key, 0) + 1

            else:
                n = clicks['dt']
                dt = datetime.datetime(n.year, n.month, n.day)
                key = (clicks['offer'], clicks['inf'].lower(), dt, clicks['country'], clicks['city'], clicks['campaignId'], clicks.get('isOnClick', True))
                bufmanyClicks[key] = bufmanyClicks.get(key, 0) + 1

        for key,value in bufbadTokenIp.items():
            db.stats_daily.update({'guid': key[0],
                                  'adv': key[1],
                                  'date': key[2],
                                  'country': key[3],
                                  'city': key[4],
                                  'campaignId': key[5],
                                  'isOnClick': key[6]},
                                  {'$set':{'badTokenIp': value}},
                                  True)

        for key,value in bufblacklistIp.items():
            db.stats_daily.update({'guid': key[0],
                                  'adv': key[1],
                                  'date': key[2],
                                  'country': key[3],
                                  'city': key[4],
                                  'campaignId': key[5],
                                  'isOnClick': key[6]},
                                  {'$set':{'blacklistIp': value}},
                                  True)
           
        for key,value in bufmanyClicks.items():
            db.stats_daily.update({'guid': key[0],
                                  'adv': key[1],
                                  'date': key[2],
                                  'country': key[3],
                                  'city': key[4],
                                  'campaignId': key[5],
                                  'isOnClick': key[6]},
                                  {'$set':{'manyClicks': value}},
                                  upsert=True, safe=True)

        print 'BadTokenCliks %s BlackListCliks %s ManyClicks %s' % (len(bufbadTokenIp), len(bufblacklistIp), len(bufmanyClicks))
        




    def importClicksFromMongo(self, db):
        u"""Обработка кликов из mongo"""
        elapsed_start_time = datetime.datetime.now()
        # _id последней записи, обработанной скриптом. Если не было обработано ничего, равно None 
        last_processed_id = None          
        try:
            last_processed_id = db.config.find_one({'key': 'clicks last _id (2)'})['value']
        except:
            last_processed_id = None
        if not isinstance(last_processed_id, bson.objectid.ObjectId):
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
            if x.get('type', 'teaser' ) == 'banner' :
                if x.get('social', False):
                    db.stats_daily.update({'guid': x['offer'],
                                           'title': x['title'],
                                           'campaignId': x['campaignId'],
                                           'adv': x['inf'],
                                           'campaignTitle': x['campaignTitle'],
                                           'country': x.get('country', 'NOT FOUND'),
                                           'city': x.get('city', 'NOT FOUND'),
                                           'isOnClick': x.get('isOnClick', True),
                                           'date': datetime.datetime.fromordinal(x['dt'].toordinal())},
                                           {'$inc': {'banner_social_clicks': 1,
                                                     'view_seconds': x.get('view_seconds', 0),
                                                     'banner_social_clicksUnique': 1 if x['unique'] else 0,
                                                     'banner_totalCost': x['cost'],
                                                     'totalCost': x['cost']}}, upsert=True, safe=True)
                else:
                    db.stats_daily.update({'guid': x['offer'],
                                           'title': x['title'],
                                           'campaignId': x['campaignId'],
                                           'adv': x['inf'],
                                           'campaignTitle': x['campaignTitle'],
                                           'country': x.get('country', 'NOT FOUND'),
                                           'city': x.get('city', 'NOT FOUND'),
                                           'isOnClick': x.get('isOnClick', True),
                                           'date': datetime.datetime.fromordinal(x['dt'].toordinal())},
                                           {'$inc': {'banner_clicks': 1,
                                                     'view_seconds': x.get('view_seconds', 0),
                                                     'banner_clicksUnique': 1 if x['unique'] else 0,
                                                     'banner_totalCost': x['cost'],
                                                     'totalCost': x['cost']}}, upsert=True, safe=True)
                if x['unique']:
                    db.offer.update({'guid': x['offer']},
                            {'$inc':{'clicks': 1, 'full_clicks':1}}, False)

                    db.stats_daily.rating.update({'adv': x['inf'] ,
                                                  'guid': x['offer'],
                                                  'campaignTitle': x['campaignTitle'],
                                                  'title': x['title'],
                                                  'campaignId': x['campaignId']},
                                                  {'$inc':{'clicks': 1, 'full_clicks':1}}, upsert=True, safe=True)
                if len(x.get('conformity','')) > 0:
                    skey = (str(x.get('branch','L0')) + '.C' + str(x['conformity']))
                else:
                    skey = (str(x.get('branch','L0')) + '.CNONE')
                db.worker_stats.update({'date': datetime.datetime.fromordinal(x['dt'].toordinal())},
                            {'$inc': {skey:1,
                                     (str(x.get('branch','L0')) + '.CALL'):1}}, upsert=True, safe=True)
            else:
                if x.get('social', False):
                    db.stats_daily.update({'guid': x['offer'],
                                           'title': x['title'],
                                           'campaignId': x['campaignId'],
                                           'adv': x['inf'],
                                           'campaignTitle': x['campaignTitle'],
                                           'country': x.get('country', 'NOT FOUND'),
                                           'city': x.get('city', 'NOT FOUND'),
                                           'isOnClick': x.get('isOnClick', True),
                                           'date': datetime.datetime.fromordinal(x['dt'].toordinal())},
                                           {'$inc': {'social_clicks': 1,
                                                     'view_seconds': x.get('view_seconds', 0),
                                                     'social_clicksUnique': 1 if x['unique'] else 0,
                                                     'teaser_totalCost': x['cost'],
                                                     'totalCost': x['cost']}}, upsert=True, safe=True)
                else:
                    db.stats_daily.update({'guid': x['offer'],
                                           'title': x['title'],
                                           'campaignId': x['campaignId'],
                                           'adv': x['inf'],
                                           'campaignTitle': x['campaignTitle'],
                                           'country': x.get('country', 'NOT FOUND'),
                                           'city': x.get('city', 'NOT FOUND'),
                                           'isOnClick': x.get('isOnClick', True),
                                           'date': datetime.datetime.fromordinal(x['dt'].toordinal())},
                                           {'$inc': {'clicks': 1,
                                                     'view_seconds': x.get('view_seconds', 0),
                                                     'clicksUnique': 1 if x['unique'] else 0,
                                                     'teaser_totalCost': x['cost'],
                                                     'totalCost': x['cost']}}, upsert=True, safe=True)
                if x['unique']:
                    db.offer.update({'guid': x['offer']},
                            {'$inc':{'clicks': 1, 'full_clicks':1}}, False)

                    db.stats_daily.rating.update({'adv': x['inf'] ,
                                                  'guid': x['offer'],
                                                  'campaignTitle': x['campaignTitle'],
                                                  'title': x['title'],
                                                  'campaignId': x['campaignId']},
                                                  {'$inc':{'clicks': 1, 'full_clicks':1}}, upsert=True, safe=True)
                if len(x.get('conformity','')) > 0:
                    skey = (str(x.get('branch','L0')) + '.C' + str(x['conformity']))
                else:
                    skey = (str(x.get('branch','L0')) + '.CNONE')
                db.worker_stats.update({'date': datetime.datetime.fromordinal(x['dt'].toordinal())},
                            {'$inc': {skey:1,
                                      (str(x.get('branch','L0')) + '.CALL'):1}}, upsert=True, safe=True)


        db.config.update({'key': 'clicks last _id (2)'}, {'$set': {'value': end_id}}, True)
        print "Finished %s records in %s seconds" % (processed_records, (datetime.datetime.now() - elapsed_start_time).seconds) 
        result_clicks = {'count': processed_records, 'elapsed_time': (datetime.datetime.now() - elapsed_start_time).seconds}
        if 'log.statisticProcess' not in db.collection_names():
            db.create_collection('log.statisticProcess',
                                    capped=True, size=50000000, max=10000)
        db.log.statisticProcess.insert({'dt': datetime.datetime.now(),
                                           'clicks': result_clicks,
                                           'srv': socket.gethostname()},
                                           safe=True)
        # Обновляем время обработки статистики
        db.config.update({'key': 'last stats_daily update date'},
                           {'$set': {'value': datetime.datetime.now()}}, safe=True)


    
    def processMongoStats(self, db, date):
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        informersBySite = {}
        informersByItemsNumber = {}
        informersByUsers = {}
        informersByTitle = {}
        for informer in db.informer.find({},{'guid' : True, 'domain' : True, 'admaker' : True, 'user': True, 'title': True}):
            userGuid = db.users.find_one({ "login": informer.get('user', 'NOT DOMAIN')},{'guid':1,'_id':0})
            domainGuid = None
            for domains in db.domain.find({ "login": informer.get('user', 'NOT DOMAIN')},{'domains':1,'_id':0}):
                for key, value in domains['domains'].items():
                    if value == informer.get('domain', 'NOT DOMAIN'):
                        domainGuid = key
            informersBySite[informer['guid']] = (informer.get('domain', 'NOT DOMAIN'), domainGuid)
            informersByItemsNumber[informer['guid']] = informer.get('admaker',{}).get('Main',{}).get('itemsNumber', 4)
            informersByUsers[informer['guid']] = (informer.get('user', 'NOT DOMAIN'), userGuid.get('guid',''))
            informersByTitle[informer['guid']] = informer.get('title', 'NOT DOMAIN')
        informers = db.stats_daily.group(

                key = ['date', 'adv', 'isOnClick'],
                condition = {'date': {'$gte': date,
                                      '$lt': date + datetime.timedelta(days=1)}},
                    reduce = '''function(obj,prev) {
                                                var impressions = obj.impressions || 0;
                                                var clicks = obj.clicks || 0;
                                                var clicksUnique = obj.clicksUnique || 0;
                                                var social_impressions = obj.social_impressions || 0;
                                                var social_clicks = obj.social_clicks || 0;
                                                var social_clicksUnique = obj.social_clicksUnique || 0;
                                                var banner_impressions = obj.banner_impressions || 0;
                                                var banner_clicks = obj.banner_clicks || 0;
                                                var banner_clicksUnique = obj.banner_clicksUnique || 0;
                                                var banner_social_impressions = obj.banner_social_impressions || 0;
                                                var banner_social_clicks = obj.banner_social_clicks || 0;
                                                var banner_social_clicksUnique = obj.banner_social_clicksUnique || 0;
                                                var view_seconds = obj.view_seconds || 0;
                                                var country = obj.country;
                                                country = country.replace(/\./, '')
                                                var city = obj.city;
                                                city = city.replace(/\./, '')

                                                prev.totalCost += obj.totalCost || 0;
                                                prev.teaser_totalCost += obj.teaser_totalCost || 0;
                                                prev.impressions += impressions;
                                                prev.clicks += clicks;
                                                prev.clicksUnique += clicksUnique;
                                                prev.social_impressions += social_impressions;
                                                prev.social_clicks += social_clicks;
                                                prev.social_clicksUnique += social_clicksUnique;
                                                prev.banner_totalCost += obj.banner_totalCost || 0;
                                                prev.banner_impressions += banner_impressions;
                                                prev.banner_clicks += banner_clicks;
                                                prev.banner_clicksUnique += banner_clicksUnique;
                                                prev.banner_social_impressions += banner_social_impressions;
                                                prev.banner_social_clicks += banner_social_clicks;
                                                prev.banner_social_clicksUnique += banner_social_clicksUnique;
                                                prev.view_seconds += view_seconds;
                                                prev.blacklistIp += obj.blacklistIp || 0;
                                                prev.badTokenIp += obj.badTokenIp || 0;
                                                prev.manyClicks += obj.manyClicks || 0;

                                                if(prev.geoImpressions[country]){
                                                    if(prev.geoImpressions[country][1][city])
                                                        prev.geoImpressions[country][1][city] += impressions;
                                                    else
                                                        prev.geoImpressions[country][1][city] = impressions;

                                                    prev.geoImpressions[country][0] += impressions;
                                                }
                                                else{
                                                    prev.geoImpressions[country] = [0,{}];

                                                    if(prev.geoImpressions[country][1][city])
                                                        prev.geoImpressions[country][1][city] += impressions;
                                                    else 
                                                        prev.geoImpressions[country][1][city] = impressions;

                                                   prev.geoImpressions[country][0] += impressions;
                                                }

                                                if(prev.geoSocialImpressions[country]){
                                                    if(prev.geoSocialImpressions[country][1][city])
                                                        prev.geoSocialImpressions[country][1][city] += social_impressions;
                                                    else
                                                        prev.geoSocialImpressions[country][1][city] = social_impressions;

                                                    prev.geoSocialImpressions[country][0] += social_impressions;
                                                }
                                                else{
                                                    prev.geoSocialImpressions[country] = [0,{}];

                                                    if(prev.geoSocialImpressions[country][1][city])
                                                        prev.geoSocialImpressions[country][1][city] += social_impressions;
                                                    else 
                                                        prev.geoSocialImpressions[country][1][city] = social_impressions;

                                                   prev.geoSocialImpressions[country][0] += social_impressions;
                                                }


                                                if(prev.geoClicks[country]){
                                                    if(prev.geoClicks[country][1][city])
                                                        prev.geoClicks[country][1][city] += clicks;
                                                    else
                                                        prev.geoClicks[country][1][city] = clicks;

                                                    prev.geoClicks[country][0] += clicks;
                                                }
                                                else{
                                                    prev.geoClicks[country] = [0,{}];

                                                    if(prev.geoClicks[country][1][city])
                                                        prev.geoClicks[country][1][city] += clicks;
                                                    else 
                                                        prev.geoClicks[country][1][city] = clicks;

                                                   prev.geoClicks[country][0] += clicks;
                                                }

                                                if(prev.geoSocialClicks[country]){
                                                    if(prev.geoSocialClicks[country][1][city])
                                                        prev.geoSocialClicks[country][1][city] += social_clicks;
                                                    else
                                                        prev.geoSocialClicks[country][1][city] = social_clicks;

                                                    prev.geoSocialClicks[country][0] += social_clicks;
                                                }
                                                else{
                                                    prev.geoSocialClicks[country] = [0,{}];

                                                    if(prev.geoSocialClicks[country][1][city])
                                                        prev.geoSocialClicks[country][1][city] += social_clicks;
                                                    else 
                                                        prev.geoSocialClicks[country][1][city] = social_clicks;

                                                   prev.geoSocialClicks[country][0] += social_clicks;
                                                }


                                                if(prev.geoClicksUnique[country]){
                                                    if(prev.geoClicksUnique[country][1][city])
                                                        prev.geoClicksUnique[country][1][city] += clicksUnique;
                                                    else
                                                        prev.geoClicksUnique[country][1][city] = clicksUnique;

                                                    prev.geoClicksUnique[country][0] += clicksUnique;
                                                }
                                                else{
                                                    prev.geoClicksUnique[country] = [0,{}];

                                                    if(prev.geoClicksUnique[country][1][city])
                                                        prev.geoClicksUnique[country][1][city] += clicksUnique;
                                                    else 
                                                        prev.geoClicksUnique[country][1][city] = clicksUnique;

                                                   prev.geoClicksUnique[country][0] += clicksUnique;
                                                }

                                                if(prev.geoSocialClicksUnique[country]){
                                                    if(prev.geoSocialClicksUnique[country][1][city])
                                                        prev.geoSocialClicksUnique[country][1][city] += social_clicksUnique;
                                                    else
                                                        prev.geoSocialClicksUnique[country][1][city] = social_clicksUnique;

                                                    prev.geoSocialClicksUnique[country][0] += social_clicksUnique;
                                                }
                                                else{
                                                    prev.geoSocialClicksUnique[country] = [0,{}];

                                                    if(prev.geoSocialClicksUnique[country][1][city])
                                                        prev.geoSocialClicksUnique[country][1][city] += social_clicksUnique;
                                                    else 
                                                        prev.geoSocialClicksUnique[country][1][city] = social_clicksUnique;

                                                   prev.geoSocialClicksUnique[country][0] += social_clicksUnique;
                                                }
                                               }''',
                    initial = {'totalCost': 0,
                               'teaser_totalCost': 0,
                               'impressions': 0,
                               'clicks': 0,
                               'clicksUnique': 0,
                               'social_impressions': 0,
                               'social_clicks': 0,
                               'social_clicksUnique': 0,
                               'banner_totalCost': 0,
                               'banner_impressions': 0,
                               'banner_clicks': 0,
                               'banner_clicksUnique': 0,
                               'banner_social_impressions': 0,
                               'banner_social_clicks': 0,
                               'banner_social_clicksUnique': 0,
                               'blacklistIp': 0,
                               'badTokenIp': 0,
                               'manyClicks': 0,
                               'geoImpressions': {},
                               'geoSocialImpressions': {},
                               'geoClicks':{},
                               'geoSocialClicks':{},
                               'geoClicksUnique':{},
                               'geoSocialClicksUnique':{},
                               'view_seconds': 0}
                    )
        for inf in informers:
            if inf['isOnClick']:
                impressions = int(inf['impressions'])
                social_impressions = int(inf['social_impressions'])
                banner_impressions = int(inf['banner_impressions'])
                banner_social_impressions = int(inf['banner_social_impressions'])
                impressions_block = ((impressions/int(informersByItemsNumber.get(inf['adv'], 4))) + banner_impressions)
                social_impressions_block = ((social_impressions/int(informersByItemsNumber.get(inf['adv'], 4))) + banner_social_impressions)
                clicksUnique = int(inf['clicksUnique'])
                banner_clicksUnique = int(inf['banner_clicksUnique'])
                social_clicksUnique = int(inf['social_clicksUnique'])
                banner_social_clicksUnique = int(inf['banner_social_clicksUnique'])
                ctr_impressions_block = 100.0 * clicksUnique / impressions_block if (clicksUnique > 0 and impressions_block > 0) else 0
                ctr_social_impressions_block = 100.0 * social_clicksUnique / social_impressions_block if (social_clicksUnique > 0 and social_impressions_block > 0) else 0
                ctr_difference_impressions_block = 100.0 * ctr_social_impressions_block / ctr_impressions_block if (ctr_social_impressions_block > 0 and ctr_impressions_block > 0) else 0
                ctr_impressions = 100.0 * clicksUnique / impressions if (clicksUnique > 0 and impressions > 0) else 0
                ctr_social_impressions = 100.0 * social_clicksUnique / social_impressions if (social_clicksUnique > 0 and social_impressions > 0) else 0
                ctr_difference_impressions = 100.0 * ctr_social_impressions / ctr_impressions if ( ctr_social_impressions > 0 and ctr_impressions > 0) else 0
                ctr_banner_impressions = 100.0 * banner_clicksUnique / banner_impressions if (banner_clicksUnique > 0 and banner_impressions > 0) else 0
                ctr_banner_social_impressions = 100.0 * banner_social_clicksUnique / banner_social_impressions if (banner_social_clicksUnique > 0 and banner_social_impressions > 0) else 0
                ctr_difference_banner_impressions = 100.0 * ctr_banner_social_impressions / ctr_banner_impressions if (ctr_banner_social_impressions > 0 and ctr_banner_impressions > 0) else 0
                db.stats_daily_adv.update(
                        {'adv': inf['adv'], 'date': inf['date'], 'isOnClick': inf['isOnClick']},
                            {'$set': {'domain': informersBySite.get(inf['adv'], 'NOT DOMAIN')[0],
                                'domain_guid': informersBySite.get(inf['adv'], 'NOT DOMAIN')[1],
                                'user': informersByUsers.get(inf['adv'], 'not user')[0],
                                'user_guid': informersByUsers.get(inf['adv'], 'not user')[1],
                                'title': informersByTitle.get(inf['adv'], 'NOT TITLE'),
                                'impressions_block': impressions_block,
                                'social_impressions_block': social_impressions_block,
                                'totalCost': inf['totalCost'],
                                'teaser_totalCost': inf['teaser_totalCost'],
                                'impressions': impressions,
                                'clicks': inf['clicks'],
                                'clicksUnique': clicksUnique,
                                'social_impressions': social_impressions,
                                'social_clicks': inf['social_clicks'],
                                'social_clicksUnique': social_clicksUnique,
                                'banner_totalCost': inf['banner_totalCost'],
                                'banner_impressions': banner_impressions,
                                'banner_clicks': inf['banner_clicks'],
                                'banner_clicksUnique': banner_clicksUnique,
                                'banner_social_impressions': banner_social_impressions,
                                'banner_social_clicks': inf['banner_social_clicks'],
                                'banner_social_clicksUnique': banner_social_clicksUnique,
                                'ctr_impressions_block': ctr_impressions_block,
                                'ctr_social_impressions_block': ctr_social_impressions_block,
                                'ctr_difference_impressions_block': ctr_difference_impressions_block,
                                'ctr_impressions': ctr_impressions,
                                'ctr_social_impressions': ctr_social_impressions,
                                'ctr_difference_impressions': ctr_difference_impressions,
                                'ctr_banner_impressions': ctr_banner_impressions,
                                'ctr_banner_social_impressions': ctr_banner_social_impressions,
                                'ctr_difference_banner_impressions': ctr_difference_banner_impressions,
                                'blacklistIp': inf['blacklistIp'],
                                'badTokenIp': inf['badTokenIp'],
                                'manyClicks': inf['manyClicks'],
                                'geoImpressions': inf['geoImpressions'],
                                'geoSocialImpressions': inf['geoSocialImpressions'],
                                'geoClicks': inf['geoClicks'],
                                'geoSocialClicks': inf['geoSocialClicks'],
                                'geoClicksUnique': inf['geoClicksUnique'],
                                'geoSocialClicksUnique': inf['geoSocialClicksUnique'],
                                'view_seconds': inf['view_seconds']
                                }},
                            upsert=True, safe=True)
            else: 
                impressions = int(inf['impressions'])
                social_impressions = int(inf['social_impressions'])
                banner_impressions = int(inf['banner_impressions'])
                banner_social_impressions = int(inf['banner_social_impressions'])
                impressions_block = ((impressions/int(informersByItemsNumber.get(inf['adv'], 4))) + banner_impressions)
                social_impressions_block = ((social_impressions/int(informersByItemsNumber.get(inf['adv'], 4))) + banner_social_impressions)
                clicksUnique = int(inf['clicksUnique'])
                banner_clicksUnique = int(inf['banner_clicksUnique'])
                social_clicksUnique = int(inf['social_clicksUnique'])
                banner_social_clicksUnique = int(inf['banner_social_clicksUnique'])
                ctr_impressions_block = 100.0 * clicksUnique / impressions_block if (clicksUnique > 0 and impressions_block > 0) else 0
                ctr_social_impressions_block = 100.0 * social_clicksUnique / social_impressions_block if (social_clicksUnique > 0 and social_impressions_block > 0) else 0
                ctr_difference_impressions_block = 100.0 * ctr_social_impressions_block / ctr_impressions_block if (ctr_social_impressions_block > 0 and ctr_impressions_block > 0) else 0
                ctr_impressions = 100.0 * clicksUnique / impressions if (clicksUnique > 0 and impressions > 0) else 0
                ctr_social_impressions = 100.0 * social_clicksUnique / social_impressions if (social_clicksUnique > 0 and social_impressions > 0) else 0
                ctr_difference_impressions = 100.0 * ctr_social_impressions / ctr_impressions if ( ctr_social_impressions > 0 and ctr_impressions > 0) else 0
                ctr_banner_impressions = 100.0 * banner_clicksUnique / banner_impressions if (banner_clicksUnique > 0 and banner_impressions > 0) else 0
                ctr_banner_social_impressions = 100.0 * banner_social_clicksUnique / banner_social_impressions if (banner_social_clicksUnique > 0 and banner_social_impressions > 0) else 0
                ctr_difference_banner_impressions = 100.0 * ctr_banner_social_impressions / ctr_banner_impressions if (ctr_banner_social_impressions > 0 and ctr_banner_impressions > 0) else 0
                db.stats_daily_adv.update(
                        {'adv': inf['adv'], 'date': inf['date'], 'isOnClick': inf['isOnClick']},
                            {'$set': {'domain': informersBySite.get(inf['adv'], 'NOT DOMAIN')[0],
                                'domain_guid': informersBySite.get(inf['adv'], 'NOT DOMAIN')[1],
                                'user': informersByUsers.get(inf['adv'], 'NOT USER')[0],
                                'user_guid': informersByUsers.get(inf['adv'], 'NOT USER')[1],
                                'title': informersByTitle.get(inf['adv'], 'NOT TITLE'),
                                'impressions_block': impressions_block,
                                'social_impressions_block': social_impressions_block,
                                'teaser_totalCost': inf['teaser_totalCost'],
                                'impressions': impressions,
                                'clicks': inf['clicks'],
                                'clicksUnique': clicksUnique,
                                'social_impressions': social_impressions,
                                'social_clicks': inf['social_clicks'],
                                'social_clicksUnique': social_clicksUnique,
                                'banner_totalCost': inf['banner_totalCost'],
                                'banner_impressions': banner_impressions,
                                'banner_clicks': inf['banner_clicks'],
                                'banner_clicksUnique': banner_clicksUnique,
                                'banner_social_impressions': banner_social_impressions,
                                'banner_social_clicks': inf['banner_social_clicks'],
                                'banner_social_clicksUnique': banner_social_clicksUnique,
                                'ctr_impressions_block': ctr_impressions_block,
                                'ctr_social_impressions_block': ctr_social_impressions_block,
                                'ctr_difference_impressions_block': ctr_difference_impressions_block,
                                'ctr_impressions': ctr_impressions,
                                'ctr_social_impressions': ctr_social_impressions,
                                'ctr_difference_impressions': ctr_difference_impressions,
                                'ctr_banner_impressions': ctr_banner_impressions,
                                'ctr_banner_social_impressions': ctr_banner_social_impressions,
                                'ctr_difference_banner_impressions': ctr_difference_banner_impressions,
                                'blacklistIp': inf['blacklistIp'],
                                'badTokenIp': inf['badTokenIp'],
                                'manyClicks': inf['manyClicks'],
                                'geoImpressions': inf['geoImpressions'],
                                'geoSocialImpressions': inf['geoSocialImpressions'],
                                'geoClicks': inf['geoClicks'],
                                'geoSocialClicks': inf['geoSocialClicks'],
                                'geoClicksUnique': inf['geoClicksUnique'],
                                'geoSocialClicksUnique': inf['geoSocialClicksUnique'],
                                'view_seconds': inf['view_seconds']
                                }},
                            upsert=True, safe=True)

        # Обновляем время обработки статистики
        db.config.update({'key': 'last stats_daily update date'},
                         {'$set': {'value': datetime.datetime.now()}}, safe=True)


    def agregateStatDailyDomain(self, db, date):
        u"""Составляет общую статистику по доменам с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date"""
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        summary = db.stats_daily_adv.group(
            key = ['date', 'domain', 'isOnClick', 'domain_guid'],
            condition = {'date': {'$gte': date,
                                  '$lt': date + datetime.timedelta(days=1)}},
            reduce = '''
                function(o, p) {
                   p.user = o.user || '';
                   p.user_guid = o.user_guid  || '';
                   p.teaser_totalCost += o.teaser_totalCost || 0;
                   p.impressions += o.impressions || 0;
                   p.impressions_block += o.impressions_block || 0;
                   p.clicks += o.clicks || 0;
                   p.clicksUnique += o.clicksUnique || 0;
                   p.social_impressions += o.social_impressions || 0;
                   p.social_impressions_block += o.social_impressions_block || 0;
                   p.social_clicks += o.social_clicks || 0;
                   p.social_clicksUnique += o.social_clicksUnique || 0;
                   p.banner_totalCost += o.banner_totalCost || 0;
                   p.banner_impressions += o.banner_impressions || 0;
                   p.banner_clicks += o.banner_clicks || 0;
                   p.banner_clicksUnique += o.banner_clicksUnique || 0;
                   p.banner_social_impressions += o.banner_social_impressions || 0;
                   p.banner_social_clicks += o.banner_social_clicks || 0;
                   p.banner_social_clicksUnique += o.banner_social_clicksUnique || 0;
                   p.view_seconds += o.view_seconds || 0;
                   p.totalCost += o.totalCost || 0;
                   p.manyClicks += o.manyClicks || 0;
                   p.badTokenIp += o.badTokenIp || 0;
                   p.blacklistIp += o.blacklistIp || 0;

                   var dataGeoImpressions = o.geoImpressions;
                   for (var key in dataGeoImpressions) {
                       var country = key;
                       var city_ar = dataGeoImpressions[country][1];
                       if (p.geoImpressions[country] == undefined){
                           p.geoImpressions[country] = [0,{}];
                           p.geoImpressions[country][0] = dataGeoImpressions[country][0];
                       }else{
                           p.geoImpressions[country][0] += dataGeoImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoImpressions[country][1][key] == undefined){
                               p.geoImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialImpressions = o.geoSocialImpressions;
                   for (var key in dataGeoSocialImpressions) {
                       var country = key;
                       var city_ar = dataGeoSocialImpressions[country][1];
                       if (p.geoSocialImpressions[country] == undefined){
                           p.geoSocialImpressions[country] = [0,{}];
                           p.geoSocialImpressions[country][0] = dataGeoSocialImpressions[country][0];
                       }else{
                           p.geoSocialImpressions[country][0] += dataGeoSocialImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialImpressions[country][1][key] == undefined){
                               p.geoSocialImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicks = o.geoClicks;
                   for (var key in dataGeoClicks) {
                       var country = key;
                       var city_ar = dataGeoClicks[country][1];
                       if (p.geoClicks[country] == undefined){
                           p.geoClicks[country] = [0,{}];
                           p.geoClicks[country][0] = dataGeoClicks[country][0];
                       }else{
                           p.geoClicks[country][0] += dataGeoClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicks[country][1][key] == undefined){
                               p.geoClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicks = o.geoSocialClicks;
                   for (var key in dataGeoSocialClicks) {
                       var country = key;
                       var city_ar = dataGeoSocialClicks[country][1];
                       if (p.geoSocialClicks[country] == undefined){
                           p.geoSocialClicks[country] = [0,{}];
                           p.geoSocialClicks[country][0] = dataGeoSocialClicks[country][0];
                       }else{
                           p.geoSocialClicks[country][0] += dataGeoSocialClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicks[country][1][key] == undefined){
                               p.geoSocialClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicksUnique = o.geoClicksUnique;
                   for (var key in dataGeoClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoClicksUnique[country][1];
                       if (p.geoClicksUnique[country] == undefined){
                           p.geoClicksUnique[country] = [0,{}];
                           p.geoClicksUnique[country][0] = dataGeoClicksUnique[country][0];
                       }else{
                           p.geoClicksUnique[country][0] += dataGeoClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicksUnique[country][1][key] == undefined){
                               p.geoClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicksUnique = o.geoSocialClicksUnique;
                   for (var key in dataGeoSocialClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoSocialClicksUnique[country][1];
                       if (p.geoSocialClicksUnique[country] == undefined){
                           p.geoSocialClicksUnique[country] = [0,{}];
                           p.geoSocialClicksUnique[country][0] = dataGeoSocialClicksUnique[country][0];
                       }else{
                           p.geoSocialClicksUnique[country][0] += dataGeoSocialClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicksUnique[country][1][key] == undefined){
                               p.geoSocialClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }
                }''',
                initial = {'user': '',
                           'user_guid': '',
                           'totalCost': 0,
                           'teaser_totalCost': 0,
                           'impressions': 0,
                           'impressions_block':0,
                           'clicks': 0,
                           'clicksUnique': 0,
                           'social_impressions': 0,
                           'social_impressions_block': 0,
                           'social_clicks': 0,
                           'social_clicksUnique': 0,
                           'banner_totalCost': 0,
                           'banner_impressions': 0,
                           'banner_clicks':0,
                           'banner_clicksUnique':0,
                           'banner_social_impressions': 0,
                           'banner_social_clicks':0,
                           'banner_social_clicksUnique':0,
                           'blacklistIp': 0, 
                           'badTokenIp': 0,
                           'manyClicks': 0,
                           'geoImpressions': {},
                           'geoSocialImpressions': {},
                           'geoClicks':{},
                           'geoSocialClicks':{},
                           'geoClicksUnique':{},
                           'geoSocialClicksUnique':{},
                           'view_seconds':0
                           }
        )
        for x in summary:
            impressions = int(x['impressions'])
            social_impressions = int(x['social_impressions'])
            banner_impressions = int(x['banner_impressions'])
            banner_social_impressions = int(x['banner_social_impressions'])
            impressions_block = int(x['impressions_block'])
            social_impressions_block = int(x['social_impressions_block'])
            clicksUnique = int(x['clicksUnique'])
            banner_clicksUnique = int(x['banner_clicksUnique'])
            social_clicksUnique = int(x['social_clicksUnique'])
            banner_social_clicksUnique = int(x['banner_social_clicksUnique'])
            ctr_impressions_block = 100.0 * clicksUnique / impressions_block if (clicksUnique > 0 and impressions_block > 0) else 0
            ctr_social_impressions_block = 100.0 * social_clicksUnique / social_impressions_block if (social_clicksUnique > 0 and social_impressions_block > 0) else 0
            ctr_difference_impressions_block = 100.0 * ctr_social_impressions_block / ctr_impressions_block if (ctr_social_impressions_block > 0 and ctr_impressions_block > 0) else 0
            ctr_impressions = 100.0 * clicksUnique / impressions if (clicksUnique > 0 and impressions > 0) else 0
            ctr_social_impressions = 100.0 * social_clicksUnique / social_impressions if (social_clicksUnique > 0 and social_impressions > 0) else 0
            ctr_difference_impressions = 100.0 * ctr_social_impressions / ctr_impressions if ( ctr_social_impressions > 0 and ctr_impressions > 0) else 0
            ctr_banner_impressions = 100.0 * banner_clicksUnique / banner_impressions if (banner_clicksUnique > 0 and banner_impressions > 0) else 0
            ctr_banner_social_impressions = 100.0 * banner_social_clicksUnique / banner_social_impressions if (banner_social_clicksUnique > 0 and banner_social_impressions > 0) else 0
            ctr_difference_banner_impressions = 100.0 * ctr_banner_social_impressions / ctr_banner_impressions if (ctr_banner_social_impressions > 0 and ctr_banner_impressions > 0) else 0
            db.stats_daily_domain.update({'date': x['date'],
                                          'domain': x['domain'],
                                          'domain_guid':x['domain_guid'],
                                          'isOnClick': x['isOnClick']},
                                              {'$set': {'user': x['user'],
                                                      'user_guid': x['user_guid'],
                                                      'totalCost': x['totalCost'],
                                                      'teaser_totalCost': x['teaser_totalCost'],
                                                      'impressions': impressions,
                                                      'impressions_block': impressions_block,
                                                      'clicks': x['clicks'],
                                                      'clicksUnique': clicksUnique,
                                                      'social_impressions': social_impressions,
                                                      'social_impressions_block': social_impressions_block,
                                                      'social_clicks': x['social_clicks'],
                                                      'social_clicksUnique':social_clicksUnique,
                                                      'banner_totalCost':x['banner_totalCost'],
                                                      'banner_impressions': banner_impressions,
                                                      'banner_clicks': x['banner_clicks'],
                                                      'banner_clicksUnique': banner_clicksUnique,
                                                      'banner_social_impressions': banner_social_impressions,
                                                      'banner_social_clicks': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique':banner_social_clicksUnique,
                                                      'ctr_impressions_block': ctr_impressions_block,
                                                      'ctr_social_impressions_block': ctr_social_impressions_block,
                                                      'ctr_difference_impressions_block': ctr_difference_impressions_block,
                                                      'ctr_impressions': ctr_impressions,
                                                      'ctr_social_impressions': ctr_social_impressions,
                                                      'ctr_difference_impressions': ctr_difference_impressions,
                                                      'ctr_banner_impressions': ctr_banner_impressions,
                                                      'ctr_banner_social_impressions': ctr_banner_social_impressions,
                                                      'ctr_difference_banner_impressions': ctr_difference_banner_impressions,
                                                      'blacklistIp': x['blacklistIp'],
                                                      'badTokenIp': x['badTokenIp'],
                                                      'manyClicks': x['manyClicks'],
                                                      'geoImpressions': x['geoImpressions'],
                                                      'geoSocialImpressions': x['geoSocialImpressions'],
                                                      'geoClicks': x['geoClicks'],
                                                      'geoSocialClicks': x['geoSocialClicks'],
                                                      'geoClicksUnique': x['geoClicksUnique'],
                                                      'geoSocialClicksUnique': x['geoSocialClicksUnique'],
                                                      'view_seconds': x['view_seconds']
                                                      }},
                                            upsert=True, safe=True)

    def agregateStatDailyUser(self, db, date):
        u"""Составляет общую статистику по доменам с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date"""
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        summary = db.stats_daily_domain.group(
            key = ['date', 'user', 'isOnClick', 'user_guid'],
            condition = {'date': {'$gte': date,
                                  '$lt': date + datetime.timedelta(days=1)}},
            reduce = '''
                function(o, p) {
                   p.teaser_totalCost += o.teaser_totalCost || 0;
                   p.impressions += o.impressions || 0;
                   p.impressions_block += o.impressions_block || 0;
                   p.clicks += o.clicks || 0;
                   p.clicksUnique += o.clicksUnique || 0;
                   p.social_impressions += o.social_impressions || 0;
                   p.social_impressions_block += o.social_impressions_block || 0;
                   p.social_clicks += o.social_clicks || 0;
                   p.social_clicksUnique += o.social_clicksUnique || 0;
                   p.banner_totalCost += o.banner_totalCost || 0;
                   p.banner_impressions += o.banner_impressions || 0;
                   p.banner_clicks += o.banner_clicks || 0;
                   p.banner_clicksUnique += o.banner_clicksUnique || 0;
                   p.banner_social_impressions += o.banner_social_impressions || 0;
                   p.banner_social_clicks += o.banner_social_clicks || 0;
                   p.banner_social_clicksUnique += o.banner_social_clicksUnique || 0;
                   p.view_seconds += o.view_seconds || 0;
                   p.totalCost += o.totalCost || 0;
                   p.manyClicks += o.manyClicks || 0;
                   p.badTokenIp += o.badTokenIp || 0;
                   p.blacklistIp += o.blacklistIp || 0;

                   var dataGeoImpressions = o.geoImpressions;
                   for (var key in dataGeoImpressions) {
                       var country = key;
                       var city_ar = dataGeoImpressions[country][1];
                       if (p.geoImpressions[country] == undefined){
                           p.geoImpressions[country] = [0,{}];
                           p.geoImpressions[country][0] = dataGeoImpressions[country][0];
                       }else{
                           p.geoImpressions[country][0] += dataGeoImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoImpressions[country][1][key] == undefined){
                               p.geoImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialImpressions = o.geoSocialImpressions;
                   for (var key in dataGeoSocialImpressions) {
                       var country = key;
                       var city_ar = dataGeoSocialImpressions[country][1];
                       if (p.geoSocialImpressions[country] == undefined){
                           p.geoSocialImpressions[country] = [0,{}];
                           p.geoSocialImpressions[country][0] = dataGeoSocialImpressions[country][0];
                       }else{
                           p.geoSocialImpressions[country][0] += dataGeoSocialImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialImpressions[country][1][key] == undefined){
                               p.geoSocialImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicks = o.geoClicks;
                   for (var key in dataGeoClicks) {
                       var country = key;
                       var city_ar = dataGeoClicks[country][1];
                       if (p.geoClicks[country] == undefined){
                           p.geoClicks[country] = [0,{}];
                           p.geoClicks[country][0] = dataGeoClicks[country][0];
                       }else{
                           p.geoClicks[country][0] += dataGeoClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicks[country][1][key] == undefined){
                               p.geoClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicks = o.geoSocialClicks;
                   for (var key in dataGeoSocialClicks) {
                       var country = key;
                       var city_ar = dataGeoSocialClicks[country][1];
                       if (p.geoSocialClicks[country] == undefined){
                           p.geoSocialClicks[country] = [0,{}];
                           p.geoSocialClicks[country][0] = dataGeoSocialClicks[country][0];
                       }else{
                           p.geoSocialClicks[country][0] += dataGeoSocialClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicks[country][1][key] == undefined){
                               p.geoSocialClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicksUnique = o.geoClicksUnique;
                   for (var key in dataGeoClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoClicksUnique[country][1];
                       if (p.geoClicksUnique[country] == undefined){
                           p.geoClicksUnique[country] = [0,{}];
                           p.geoClicksUnique[country][0] = dataGeoClicksUnique[country][0];
                       }else{
                           p.geoClicksUnique[country][0] += dataGeoClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicksUnique[country][1][key] == undefined){
                               p.geoClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicksUnique = o.geoSocialClicksUnique;
                   for (var key in dataGeoSocialClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoSocialClicksUnique[country][1];
                       if (p.geoSocialClicksUnique[country] == undefined){
                           p.geoSocialClicksUnique[country] = [0,{}];
                           p.geoSocialClicksUnique[country][0] = dataGeoSocialClicksUnique[country][0];
                       }else{
                           p.geoSocialClicksUnique[country][0] += dataGeoSocialClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicksUnique[country][1][key] == undefined){
                               p.geoSocialClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }
                }''',
                initial = {'totalCost': 0,
                           'teaser_totalCost': 0,
                           'impressions': 0,
                           'impressions_block':0,
                           'clicks': 0,
                           'clicksUnique': 0,
                           'social_impressions': 0,
                           'social_impressions_block': 0,
                           'social_clicks': 0,
                           'social_clicksUnique': 0,
                           'banner_totalCost': 0,
                           'banner_impressions': 0,
                           'banner_clicks':0,
                           'banner_clicksUnique':0,
                           'banner_social_impressions': 0,
                           'banner_social_clicks':0,
                           'banner_social_clicksUnique':0,
                           'blacklistIp': 0, 
                           'badTokenIp': 0,
                           'manyClicks': 0,
                           'geoImpressions': {},
                           'geoSocialImpressions': {},
                           'geoClicks':{},
                           'geoSocialClicks':{},
                           'geoClicksUnique':{},
                           'geoSocialClicksUnique':{},
                           'view_seconds':0
                           }
        )
        for x in summary:
            impressions = int(x['impressions'])
            social_impressions = int(x['social_impressions'])
            banner_impressions = int(x['banner_impressions'])
            banner_social_impressions = int(x['banner_social_impressions'])
            impressions_block = int(x['impressions_block'])
            social_impressions_block = int(x['social_impressions_block'])
            clicksUnique = int(x['clicksUnique'])
            banner_clicksUnique = int(x['banner_clicksUnique'])
            social_clicksUnique = int(x['social_clicksUnique'])
            banner_social_clicksUnique = int(x['banner_social_clicksUnique'])
            ctr_impressions_block = 100.0 * clicksUnique / impressions_block if (clicksUnique > 0 and impressions_block > 0) else 0
            ctr_social_impressions_block = 100.0 * social_clicksUnique / social_impressions_block if (social_clicksUnique > 0 and social_impressions_block > 0) else 0
            ctr_difference_impressions_block = 100.0 * ctr_social_impressions_block / ctr_impressions_block if (ctr_social_impressions_block > 0 and ctr_impressions_block > 0) else 0
            ctr_impressions = 100.0 * clicksUnique / impressions if (clicksUnique > 0 and impressions > 0) else 0
            ctr_social_impressions = 100.0 * social_clicksUnique / social_impressions if (social_clicksUnique > 0 and social_impressions > 0) else 0
            ctr_difference_impressions = 100.0 * ctr_social_impressions / ctr_impressions if ( ctr_social_impressions > 0 and ctr_impressions > 0) else 0
            ctr_banner_impressions = 100.0 * banner_clicksUnique / banner_impressions if (banner_clicksUnique > 0 and banner_impressions > 0) else 0
            ctr_banner_social_impressions = 100.0 * banner_social_clicksUnique / banner_social_impressions if (banner_social_clicksUnique > 0 and banner_social_impressions > 0) else 0
            ctr_difference_banner_impressions = 100.0 * ctr_banner_social_impressions / ctr_banner_impressions if (ctr_banner_social_impressions > 0 and ctr_banner_impressions > 0) else 0
            db.stats_daily_user.update({'date': x['date'],
                                        'user': x['user'],
                                        'user_guid': x['user_guid'],
                                        'isOnClick': x['isOnClick']},
                                              {'$set': {'totalCost': x['totalCost'],
                                                      'teaser_totalCost': x['teaser_totalCost'],
                                                      'impressions': impressions,
                                                      'impressions_block': impressions_block,
                                                      'clicks': x['clicks'],
                                                      'clicksUnique': clicksUnique,
                                                      'social_impressions': social_impressions,
                                                      'social_impressions_block': social_impressions_block,
                                                      'social_clicks': x['social_clicks'],
                                                      'social_clicksUnique': social_clicksUnique,
                                                      'banner_totalCost': x['banner_totalCost'],
                                                      'banner_impressions': banner_impressions,
                                                      'banner_clicks': x['banner_clicks'],
                                                      'banner_clicksUnique': banner_clicksUnique,
                                                      'banner_social_impressions': banner_social_impressions,
                                                      'banner_social_clicks': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique': banner_social_clicksUnique,
                                                      'ctr_impressions_block': ctr_impressions_block,
                                                      'ctr_social_impressions_block': ctr_social_impressions_block,
                                                      'ctr_difference_impressions_block': ctr_difference_impressions_block,
                                                      'ctr_impressions': ctr_impressions,
                                                      'ctr_social_impressions': ctr_social_impressions,
                                                      'ctr_difference_impressions': ctr_difference_impressions,
                                                      'ctr_banner_impressions': ctr_banner_impressions,
                                                      'ctr_banner_social_impressions': ctr_banner_social_impressions,
                                                      'ctr_difference_banner_impressions': ctr_difference_banner_impressions,
                                                      'blacklistIp': x['blacklistIp'],
                                                      'badTokenIp': x['badTokenIp'],
                                                      'manyClicks': x['manyClicks'],
                                                      'geoImpressions': x['geoImpressions'],
                                                      'geoSocialImpressions': x['geoSocialImpressions'],
                                                      'geoClicks': x['geoClicks'],
                                                      'geoSocialClicks': x['geoSocialClicks'],
                                                      'geoClicksUnique': x['geoClicksUnique'],
                                                      'geoSocialClicksUnique': x['geoSocialClicksUnique'],
                                                      'view_seconds': x['view_seconds']
                                                      }},
                                            upsert=True, safe=True)

    def agregateStatDailyAll(self, db, date):
        u"""Составляет общую статистику по доменам с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date"""
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        summary = db.stats_daily_user.group(
            key = ['date'],
            condition = {'date': {'$gte': date,
                                  '$lt': date + datetime.timedelta(days=1)}},
            reduce = '''
                function(o, p) {
                   p.teaser_totalCost += o.teaser_totalCost || 0;
                   p.impressions += o.impressions || 0;
                   p.impressions_block += o.impressions_block || 0;
                   p.clicks += o.clicks || 0;
                   p.clicksUnique += o.clicksUnique || 0;
                   p.social_impressions += o.social_impressions || 0;
                   p.social_impressions_block += o.social_impressions_block || 0;
                   p.social_clicks += o.social_clicks || 0;
                   p.social_clicksUnique += o.social_clicksUnique || 0;
                   if (o.isOnClick){
                   p.banner_totalCost += o.banner_totalCost || 0;
                   p.banner_impressions += o.banner_impressions || 0;
                   p.banner_clicks += o.banner_clicks || 0;
                   p.banner_clicksUnique += o.banner_clicksUnique || 0;
                   p.banner_social_impressions += o.banner_social_impressions || 0;
                   p.banner_social_clicks += o.banner_social_clicks || 0;
                   p.banner_social_clicksUnique += o.banner_social_clicksUnique || 0;
                   }
                   else{
                   p.imp_banner_totalCost += o.banner_totalCost || o.totalCost || 0;
                   p.imp_banner_impressions += o.banner_impressions || 0;
                   p.imp_banner_clicks += o.banner_clicks || 0;
                   p.imp_banner_clicksUnique += o.banner_clicksUnique || 0;
                   p.imp_banner_social_impressions += o.banner_social_impressions || 0;
                   p.imp_banner_social_clicks += o.banner_social_clicks || 0;
                   p.imp_banner_social_clicksUnique += o.banner_social_clicksUnique || 0;
                   }
                   p.view_seconds += o.view_seconds || 0;
                   p.totalCost += o.totalCost || 0;
                   p.manyClicks += o.manyClicks || 0;
                   p.badTokenIp += o.badTokenIp || 0;
                   p.blacklistIp += o.blacklistIp || 0;

                   var dataGeoImpressions = o.geoImpressions;
                   for (var key in dataGeoImpressions) {
                       var country = key;
                       var city_ar = dataGeoImpressions[country][1];
                       if (p.geoImpressions[country] == undefined){
                           p.geoImpressions[country] = [0,{}];
                           p.geoImpressions[country][0] = dataGeoImpressions[country][0];
                       }else{
                           p.geoImpressions[country][0] += dataGeoImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoImpressions[country][1][key] == undefined){
                               p.geoImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialImpressions = o.geoSocialImpressions;
                   for (var key in dataGeoSocialImpressions) {
                       var country = key;
                       var city_ar = dataGeoSocialImpressions[country][1];
                       if (p.geoSocialImpressions[country] == undefined){
                           p.geoSocialImpressions[country] = [0,{}];
                           p.geoSocialImpressions[country][0] = dataGeoSocialImpressions[country][0];
                       }else{
                           p.geoSocialImpressions[country][0] += dataGeoSocialImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialImpressions[country][1][key] == undefined){
                               p.geoSocialImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicks = o.geoClicks;
                   for (var key in dataGeoClicks) {
                       var country = key;
                       var city_ar = dataGeoClicks[country][1];
                       if (p.geoClicks[country] == undefined){
                           p.geoClicks[country] = [0,{}];
                           p.geoClicks[country][0] = dataGeoClicks[country][0];
                       }else{
                           p.geoClicks[country][0] += dataGeoClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicks[country][1][key] == undefined){
                               p.geoClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicks = o.geoSocialClicks;
                   for (var key in dataGeoSocialClicks) {
                       var country = key;
                       var city_ar = dataGeoSocialClicks[country][1];
                       if (p.geoSocialClicks[country] == undefined){
                           p.geoSocialClicks[country] = [0,{}];
                           p.geoSocialClicks[country][0] = dataGeoSocialClicks[country][0];
                       }else{
                           p.geoSocialClicks[country][0] += dataGeoSocialClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicks[country][1][key] == undefined){
                               p.geoSocialClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicksUnique = o.geoClicksUnique;
                   for (var key in dataGeoClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoClicksUnique[country][1];
                       if (p.geoClicksUnique[country] == undefined){
                           p.geoClicksUnique[country] = [0,{}];
                           p.geoClicksUnique[country][0] = dataGeoClicksUnique[country][0];
                       }else{
                           p.geoClicksUnique[country][0] += dataGeoClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicksUnique[country][1][key] == undefined){
                               p.geoClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicksUnique = o.geoSocialClicksUnique;
                   for (var key in dataGeoSocialClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoSocialClicksUnique[country][1];
                       if (p.geoSocialClicksUnique[country] == undefined){
                           p.geoSocialClicksUnique[country] = [0,{}];
                           p.geoSocialClicksUnique[country][0] = dataGeoSocialClicksUnique[country][0];
                       }else{
                           p.geoSocialClicksUnique[country][0] += dataGeoSocialClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicksUnique[country][1][key] == undefined){
                               p.geoSocialClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }
                }''',
                initial = {'totalCost': 0,
                           'teaser_totalCost': 0,
                           'impressions': 0,
                           'impressions_block':0,
                           'clicks': 0,
                           'clicksUnique': 0,
                           'social_impressions': 0,
                           'social_impressions_block': 0,
                           'social_clicks': 0,
                           'social_clicksUnique': 0,
                           'banner_totalCost': 0,
                           'banner_impressions': 0,
                           'banner_clicks':0,
                           'banner_clicksUnique':0,
                           'banner_social_impressions': 0,
                           'banner_social_clicks':0,
                           'banner_social_clicksUnique':0,
                           'imp_banner_totalCost': 0,
                           'imp_banner_impressions': 0,
                           'imp_banner_clicks': 0,
                           'imp_banner_clicksUnique': 0,
                           'imp_banner_social_impressions': 0,
                           'imp_banner_social_clicks': 0,
                           'imp_banner_social_clicksUnique': 0,
                           'blacklistIp': 0, 
                           'badTokenIp': 0,
                           'manyClicks': 0,
                           'geoImpressions': {},
                           'geoSocialImpressions': {},
                           'geoClicks':{},
                           'geoSocialClicks':{},
                           'geoClicksUnique':{},
                           'geoSocialClicksUnique':{},
                           'view_seconds':0
                           }
        )
        for x in summary:
            impressions = int(x['impressions'])
            social_impressions = int(x['social_impressions'])
            banner_impressions = int(x['banner_impressions'])
            banner_social_impressions = int(x['banner_social_impressions'])
            impressions_block = int(x['impressions_block'])
            social_impressions_block = int(x['social_impressions_block'])
            clicksUnique = int(x['clicksUnique'])
            banner_clicksUnique = int(x['banner_clicksUnique'])
            social_clicksUnique = int(x['social_clicksUnique'])
            banner_social_clicksUnique = int(x['banner_social_clicksUnique'])
            ctr_impressions_block = 100.0 * clicksUnique / impressions_block if (clicksUnique > 0 and impressions_block > 0) else 0
            ctr_social_impressions_block = 100.0 * social_clicksUnique / social_impressions_block if (social_clicksUnique > 0 and social_impressions_block > 0) else 0
            ctr_difference_impressions_block = 100.0 * ctr_social_impressions_block / ctr_impressions_block if (ctr_social_impressions_block > 0 and ctr_impressions_block > 0) else 0
            ctr_impressions = 100.0 * clicksUnique / impressions if (clicksUnique > 0 and impressions > 0) else 0
            ctr_social_impressions = 100.0 * social_clicksUnique / social_impressions if (social_clicksUnique > 0 and social_impressions > 0) else 0
            ctr_difference_impressions = 100.0 * ctr_social_impressions / ctr_impressions if ( ctr_social_impressions > 0 and ctr_impressions > 0) else 0
            ctr_banner_impressions = 100.0 * banner_clicksUnique / banner_impressions if (banner_clicksUnique > 0 and banner_impressions > 0) else 0
            ctr_banner_social_impressions = 100.0 * banner_social_clicksUnique / banner_social_impressions if (banner_social_clicksUnique > 0 and banner_social_impressions > 0) else 0
            ctr_difference_banner_impressions = 100.0 * ctr_banner_social_impressions / ctr_banner_impressions if (ctr_banner_social_impressions > 0 and ctr_banner_impressions > 0) else 0
            db.stats_daily_all.update({'date': x['date']},
                                              {'$set': {'totalCost': x['totalCost'],
                                                      'teaser_totalCost': x['teaser_totalCost'],
                                                      'impressions': impressions,
                                                      'impressions_block': impressions_block,
                                                      'clicks': x['clicks'],
                                                      'clicksUnique': clicksUnique,
                                                      'social_impressions': social_impressions,
                                                      'social_impressions_block': social_impressions_block,
                                                      'social_clicks': x['social_clicks'],
                                                      'social_clicksUnique': social_clicksUnique,
                                                      'banner_totalCost': x['banner_totalCost'],
                                                      'banner_impressions': banner_impressions,
                                                      'banner_clicks': x['banner_clicks'],
                                                      'banner_clicksUnique': banner_clicksUnique,
                                                      'banner_social_impressions': banner_social_impressions,
                                                      'banner_social_clicks': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique': banner_social_clicksUnique,
                                                      'imp_banner_totalCost': x['imp_banner_totalCost'],
                                                      'imp_banner_impressions': x['imp_banner_impressions'],
                                                      'imp_banner_clicks': x['imp_banner_clicks'],
                                                      'imp_banner_clicksUnique': x['imp_banner_clicksUnique'],
                                                      'imp_banner_social_impressions': x['imp_banner_social_impressions'],
                                                      'imp_banner_social_clicks': x['imp_banner_social_clicks'],
                                                      'imp_banner_social_clicksUnique': x['imp_banner_social_clicksUnique'],
                                                      'ctr_impressions_block': ctr_impressions_block,
                                                      'ctr_social_impressions_block': ctr_social_impressions_block,
                                                      'ctr_difference_impressions_block': ctr_difference_impressions_block,
                                                      'ctr_impressions': ctr_impressions,
                                                      'ctr_social_impressions': ctr_social_impressions,
                                                      'ctr_difference_impressions': ctr_difference_impressions,
                                                      'ctr_banner_impressions': ctr_banner_impressions,
                                                      'ctr_banner_social_impressions': ctr_banner_social_impressions,
                                                      'ctr_difference_banner_impressions': ctr_difference_banner_impressions,
                                                      'blacklistIp': x['blacklistIp'],
                                                      'badTokenIp': x['badTokenIp'],
                                                      'manyClicks': x['manyClicks'],
                                                      'geoImpressions': x['geoImpressions'],
                                                      'geoSocialImpressions': x['geoSocialImpressions'],
                                                      'geoClicks': x['geoClicks'],
                                                      'geoSocialClicks': x['geoSocialClicks'],
                                                      'geoClicksUnique': x['geoClicksUnique'],
                                                      'geoSocialClicksUnique': x['geoSocialClicksUnique'],
                                                      'view_seconds': x['view_seconds']
                                                      }},
                                            upsert=True, safe=True)

    def agregateStatUserSummary(self, db, date):
        u"""Составляет общую статистику по доменам с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date"""
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        condition1 = {'date': {'$gte': date, '$lt': date + datetime.timedelta(days=1)}}
        condition2 = {'date': {'$gte': date - datetime.timedelta(days=1), '$lt': date}}
        condition3 = {'date': {'$gte': date - datetime.timedelta(days=2), '$lt': date - datetime.timedelta(days=1)}}
        condition7 = {'date': {'$gte': date - datetime.timedelta(days=7), '$lt': date + datetime.timedelta(days=1)}}
        condition30 = {'date': {'$gte': date - datetime.timedelta(days=30), '$lt': date + datetime.timedelta(days=1)}}
        condition365 = {'date': {'$gte': date - datetime.timedelta(days=365), '$lt': date + datetime.timedelta(days=1)}}
        filds = {'geoClicks': False, 'geoClicksUnique': False, 'geoImpressions': False,'geoSocialClicks': False,\
                                'geoSocialClicksUnique': False, 'geoSocialImpressions': False}
        userStats = db.users.group(key={'login':True}, condition={'manager':False}, reduce='function(obj,prev){}', initial={})
        userStats = map(lambda x: x['login'], userStats)
        userStats1 = userStats
        userStats2 = userStats
        userStats3 = userStats
        userStats7 = userStats
        userStats30 = userStats
        userStats365 = userStats
        reduce = '''
                function(o, p) {
                   p.totalCost += o.totalCost || 0;
                   p.teaser_totalCost += o.teaser_totalCost || 0;
                   p.impressions += o.impressions || 0;
                   p.impressions_block += o.impressions_block || 0;
                   p.clicks += o.clicks || 0;
                   p.clicksUnique += o.clicksUnique || 0;
                   p.social_impressions += o.social_impressions || 0;
                   p.social_impressions_block += o.social_impressions_block || 0;
                   p.social_clicks += o.social_clicks || 0;
                   p.social_clicksUnique += o.social_clicksUnique || 0;
                   if (o.isOnClick){
                   p.banner_totalCost += o.banner_totalCost || 0;
                   p.banner_impressions += o.banner_impressions || 0;
                   p.banner_clicks += o.banner_clicks || 0;
                   p.banner_clicksUnique += o.banner_clicksUnique || 0;
                   p.banner_social_impressions += o.banner_social_impressions || 0;
                   p.banner_social_clicks += o.banner_social_clicks || 0;
                   p.banner_social_clicksUnique += o.banner_social_clicksUnique || 0;
                   }
                   else{
                   p.imp_banner_totalCost += o.banner_totalCost || o.totalCost || 0;
                   p.imp_banner_impressions += o.banner_impressions || 0;
                   p.imp_banner_clicks += o.banner_clicks || 0;
                   p.imp_banner_clicksUnique += o.banner_clicksUnique || 0;
                   p.imp_banner_social_impressions += o.banner_social_impressions || 0;
                   p.imp_banner_social_clicks += o.banner_social_clicks || 0;
                   p.imp_banner_social_clicksUnique += o.banner_social_clicksUnique || 0;
                   }
                }'''
        initial = {'totalCost': 0,
                   'teaser_totalCost': 0,
                   'impressions': 0,
                   'impressions_block':0,
                   'clicks': 0,
                   'clicksUnique': 0,
                   'social_impressions': 0,
                   'social_impressions_block': 0,
                   'social_clicks': 0,
                   'social_clicksUnique': 0,
                   'banner_totalCost': 0,
                   'banner_impressions': 0,
                   'banner_clicks':0,
                   'banner_clicksUnique':0,
                   'banner_social_impressions': 0,
                   'banner_social_clicks':0,
                   'banner_social_clicksUnique':0,
                   'imp_banner_totalCost': 0,
                   'imp_banner_impressions': 0,
                   'imp_banner_clicks': 0,
                   'imp_banner_clicksUnique': 0,
                   'imp_banner_social_impressions': 0,
                   'imp_banner_social_clicks': 0,
                   'imp_banner_social_clicksUnique': 0
                   }
        cur1 = db.stats_daily_user.group(
            key = ['user'],
            condition = condition1,
            reduce = reduce,
            initial = initial
        )
        cur2 = db.stats_daily_user.group(
            key = ['user'],
            condition = condition2,
            reduce = reduce,
            initial = initial
        )
        cur3 = db.stats_daily_user.group(
            key = ['user'],
            condition = condition3,
            reduce = reduce,
            initial = initial
        )
        cur7 = db.stats_daily_user.group(
            key = ['user'],
            condition = condition7,
            reduce = reduce,
            initial = initial
        )
        cur30 = db.stats_daily_user.group(
            key = ['user'],
            condition = condition30,
            reduce = reduce,
            initial = initial
        )
        cur365 = db.stats_daily_user.group(
            key = ['user'],
            condition = condition365,
            reduce = reduce,
            initial = initial
        )
        for x in cur1:
            db.stats_user_summary.update({'user': x['user']},
                                              {'$set': {'totalCost': x['totalCost'],
                                                      'teaser_totalCost': x['teaser_totalCost'],
                                                      'impressions': x['impressions'],
                                                      'impressions_block': x['impressions_block'],
                                                      'clicks': x['clicks'],
                                                      'clicksUnique': x['clicksUnique'],
                                                      'social_impressions': x['social_impressions'],
                                                      'social_impressions_block': x['social_impressions_block'],
                                                      'social_clicks': x['social_clicks'],
                                                      'social_clicksUnique':x['social_clicksUnique'],
                                                      'banner_totalCost': x['banner_totalCost'],
                                                      'banner_impressions': x['banner_impressions'],
                                                      'banner_clicks': x['banner_clicks'],
                                                      'banner_clicksUnique': x['banner_clicksUnique'],
                                                      'banner_social_impressions': x['banner_social_impressions'],
                                                      'banner_social_clicks': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique':x['banner_social_clicksUnique'],
                                                      'imp_banner_totalCost': x['imp_banner_totalCost'],
                                                      'imp_banner_impressions': x['imp_banner_impressions'],
                                                      'imp_banner_clicks': x['imp_banner_clicks'],
                                                      'imp_banner_clicksUnique': x['imp_banner_clicksUnique'],
                                                      'imp_banner_social_impressions': x['imp_banner_social_impressions'],
                                                      'imp_banner_social_clicks': x['imp_banner_social_clicks'],
                                                      'imp_banner_social_clicksUnique': x['imp_banner_social_clicksUnique']
                                                      }},
                                            upsert=True, safe=True)
            if x['user'] in userStats1:
                userStats1.remove(x['user'])
        for x in userStats1:
            db.stats_user_summary.update({'user': x},
                                              {'$set': {'totalCost': 0,
                                                      'teaser_totalCost': 0,
                                                      'impressions': 0,
                                                      'impressions_block': 0,
                                                      'clicks': 0,
                                                      'clicksUnique': 0,
                                                      'social_impressions': 0,
                                                      'social_impressions_block': 0,
                                                      'social_clicks': 0,
                                                      'social_clicksUnique':0,
                                                      'banner_totalCost': 0,
                                                      'banner_impressions': 0,
                                                      'banner_clicks': 0,
                                                      'banner_clicksUnique': 0,
                                                      'banner_social_impressions': 0,
                                                      'banner_social_clicks': 0,
                                                      'banner_social_clicksUnique': 0,
                                                      'imp_banner_totalCost': 0,
                                                      'imp_banner_impressions': 0,
                                                      'imp_banner_clicks': 0,
                                                      'imp_banner_clicksUnique': 0,
                                                      'imp_banner_social_impressions': 0,
                                                      'imp_banner_social_clicks': 0,
                                                      'imp_banner_social_clicksUnique': 0
                                                      }},
                                            upsert=True, safe=True)
        for x in cur2:
            db.stats_user_summary.update({'user': x['user']},
                                              {'$set': {'totalCost_2': x['totalCost'],
                                                      'teaser_totalCost_2': x['teaser_totalCost'],
                                                      'impressions_2': x['impressions'],
                                                      'impressions_block_2': x['impressions_block'],
                                                      'clicks_2': x['clicks'],
                                                      'clicksUnique_2': x['clicksUnique'],
                                                      'social_impressions_2': x['social_impressions'],
                                                      'social_impressions_block_2': x['social_impressions_block'],
                                                      'social_clicks_2': x['social_clicks'],
                                                      'social_clicksUnique_2':x['social_clicksUnique'],
                                                      'banner_totalCost_2': x['banner_totalCost'],
                                                      'banner_impressions_2': x['banner_impressions'],
                                                      'banner_clicks_2': x['banner_clicks'],
                                                      'banner_clicksUnique_2': x['banner_clicksUnique'],
                                                      'banner_social_impressions_2': x['banner_social_impressions'],
                                                      'banner_social_clicks_2': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique_2':x['banner_social_clicksUnique'],
                                                      'imp_banner_totalCost_2': x['imp_banner_totalCost'],
                                                      'imp_banner_impressions_2': x['imp_banner_impressions'],
                                                      'imp_banner_clicks_2': x['imp_banner_clicks'],
                                                      'imp_banner_clicksUnique_2': x['imp_banner_clicksUnique'],
                                                      'imp_banner_social_impressions_2': x['imp_banner_social_impressions'],
                                                      'imp_banner_social_clicks_2': x['imp_banner_social_clicks'],
                                                      'imp_banner_social_clicksUnique_2': x['imp_banner_social_clicksUnique']
                                                      }},
                                            upsert=True, safe=True)
            if x['user'] in userStats2:
                userStats2.remove(x['user'])
        for x in userStats2:
            db.stats_user_summary.update({'user': x},
                                              {'$set': {'totalCost_2': 0,
                                                      'teaser_totalCost_2': 0,
                                                      'impressions_2': 0,
                                                      'impressions_block_2': 0,
                                                      'clicks_2': 0,
                                                      'clicksUnique_2': 0,
                                                      'social_impressions_2': 0,
                                                      'social_impressions_block_2': 0,
                                                      'social_clicks_2': 0,
                                                      'social_clicksUnique_2': 0,
                                                      'banner_totalCost_2': 0,
                                                      'banner_impressions_2': 0,
                                                      'banner_clicks_2': 0,
                                                      'banner_clicksUnique_2': 0,
                                                      'banner_social_impressions_2': 0,
                                                      'banner_social_clicks_2': 0,
                                                      'banner_social_clicksUnique_2': 0,
                                                      'imp_banner_totalCost_2': 0,
                                                      'imp_banner_impressions_2': 0,
                                                      'imp_banner_clicks_2': 0,
                                                      'imp_banner_clicksUnique_2': 0,
                                                      'imp_banner_social_impressions_2': 0,
                                                      'imp_banner_social_clicks_2': 0,
                                                      'imp_banner_social_clicksUnique_2': 0
                                                      }},
                                            upsert=True, safe=True)

        for x in cur3:
            db.stats_user_summary.update({'user': x['user']},
                                              {'$set': {'totalCost_3': x['totalCost'],
                                                      'teaser_totalCost_3': x['teaser_totalCost'],
                                                      'impressions_3': x['impressions'],
                                                      'impressions_block_3': x['impressions_block'],
                                                      'clicks_3': x['clicks'],
                                                      'clicksUnique_3': x['clicksUnique'],
                                                      'social_impressions_3': x['social_impressions'],
                                                      'social_impressions_block_3': x['social_impressions_block'],
                                                      'social_clicks_3': x['social_clicks'],
                                                      'social_clicksUnique_3':x['social_clicksUnique'],
                                                      'banner_totalCost_3': x['banner_totalCost'],
                                                      'banner_impressions_3': x['banner_impressions'],
                                                      'banner_clicks_3': x['banner_clicks'],
                                                      'banner_clicksUnique_3': x['banner_clicksUnique'],
                                                      'banner_social_impressions_3': x['banner_social_impressions'],
                                                      'banner_social_clicks_3': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique_3':x['banner_social_clicksUnique'],
                                                      'imp_banner_totalCost_3': x['imp_banner_totalCost'],
                                                      'imp_banner_impressions_3': x['imp_banner_impressions'],
                                                      'imp_banner_clicks_3': x['imp_banner_clicks'],
                                                      'imp_banner_clicksUnique_3': x['imp_banner_clicksUnique'],
                                                      'imp_banner_social_impressions_3': x['imp_banner_social_impressions'],
                                                      'imp_banner_social_clicks_3': x['imp_banner_social_clicks'],
                                                      'imp_banner_social_clicksUnique_3': x['imp_banner_social_clicksUnique']
                                                      }},
                                            upsert=True, safe=True)
            if x['user'] in userStats3:
                userStats3.remove(x['user'])
        for x in userStats3:
            db.stats_user_summary.update({'user': x},
                                              {'$set': {'totalCost_3': 0,
                                                      'teaser_totalCost_3': 0,
                                                      'impressions_3': 0,
                                                      'impressions_block_3': 0,
                                                      'clicks_3': 0,
                                                      'clicksUnique_3': 0,
                                                      'social_impressions_3': 0,
                                                      'social_impressions_block_3': 0,
                                                      'social_clicks_3': 0,
                                                      'social_clicksUnique_3': 0,
                                                      'banner_totalCost_3': 0,
                                                      'banner_impressions_3': 0,
                                                      'banner_clicks_3': 0,
                                                      'banner_clicksUnique_3': 0,
                                                      'banner_social_impressions_3': 0,
                                                      'banner_social_clicks_3': 0,
                                                      'banner_social_clicksUnique_3': 0,
                                                      'imp_banner_totalCost_3': 0,
                                                      'imp_banner_impressions_3': 0,
                                                      'imp_banner_clicks_3': 0,
                                                      'imp_banner_clicksUnique_3': 0,
                                                      'imp_banner_social_impressions_3': 0,
                                                      'imp_banner_social_clicks_3': 0,
                                                      'imp_banner_social_clicksUnique_3': 0
                                                      }},
                                            upsert=True, safe=True)


        for x in cur7:
            db.stats_user_summary.update({'user': x['user']},
                                              {'$set': {'totalCost_7': x['totalCost'],
                                                      'teaser_totalCost_7': x['teaser_totalCost'],
                                                      'impressions_7': x['impressions'],
                                                      'impressions_block_7': x['impressions_block'],
                                                      'clicks_7': x['clicks'],
                                                      'clicksUnique_7': x['clicksUnique'],
                                                      'social_impressions_7': x['social_impressions'],
                                                      'social_impressions_block_7': x['social_impressions_block'],
                                                      'social_clicks_7': x['social_clicks'],
                                                      'social_clicksUnique_7':x['social_clicksUnique'],
                                                      'banner_totalCost_7': x['banner_totalCost'],
                                                      'banner_impressions_7': x['banner_impressions'],
                                                      'banner_clicks_7': x['banner_clicks'],
                                                      'banner_clicksUnique_7': x['banner_clicksUnique'],
                                                      'banner_social_impressions_7': x['banner_social_impressions'],
                                                      'banner_social_clicks_7': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique_7':x['banner_social_clicksUnique'],
                                                      'imp_banner_totalCost_7': x['imp_banner_totalCost'],
                                                      'imp_banner_impressions_7': x['imp_banner_impressions'],
                                                      'imp_banner_clicks_7': x['imp_banner_clicks'],
                                                      'imp_banner_clicksUnique_7': x['imp_banner_clicksUnique'],
                                                      'imp_banner_social_impressions_7': x['imp_banner_social_impressions'],
                                                      'imp_banner_social_clicks_7': x['imp_banner_social_clicks'],
                                                      'imp_banner_social_clicksUnique_7': x['imp_banner_social_clicksUnique']
                                                      }},
                                            upsert=True, safe=True)
            if x['user'] in userStats7:
                userStats7.remove(x['user'])
        for x in userStats7:
            db.stats_user_summary.update({'user': x},
                                              {'$set': {'totalCost_7': 0,
                                                      'teaser_totalCost_7': 0,
                                                      'impressions_7': 0,
                                                      'impressions_block_7': 0,
                                                      'clicks_7': 0,
                                                      'clicksUnique_7': 0,
                                                      'social_impressions_7': 0,
                                                      'social_impressions_block_7': 0,
                                                      'social_clicks_7': 0,
                                                      'social_clicksUnique_7': 0,
                                                      'banner_totalCost_7': 0,
                                                      'banner_impressions_7': 0,
                                                      'banner_clicks_7': 0,
                                                      'banner_clicksUnique_7': 0,
                                                      'banner_social_impressions_7': 0,
                                                      'banner_social_clicks_7': 0,
                                                      'banner_social_clicksUnique_7': 0,
                                                      'imp_banner_totalCost_7': 0,
                                                      'imp_banner_impressions_7': 0,
                                                      'imp_banner_clicks_7': 0,
                                                      'imp_banner_clicksUnique_7': 0,
                                                      'imp_banner_social_impressions_7': 0,
                                                      'imp_banner_social_clicks_7': 0,
                                                      'imp_banner_social_clicksUnique_7': 0
                                                      }},
                                            upsert=True, safe=True)

        for x in cur30:
            db.stats_user_summary.update({'user': x['user']},
                                              {'$set': {'totalCost_30': x['totalCost'],
                                                      'teaser_totalCost_30': x['teaser_totalCost'],
                                                      'impressions_30': x['impressions'],
                                                      'impressions_block_30': x['impressions_block'],
                                                      'clicks_30': x['clicks'],
                                                      'clicksUnique_30': x['clicksUnique'],
                                                      'social_impressions_30': x['social_impressions'],
                                                      'social_impressions_block_30': x['social_impressions_block'],
                                                      'social_clicks_30': x['social_clicks'],
                                                      'social_clicksUnique_30':x['social_clicksUnique'],
                                                      'banner_totalCost_30': x['banner_totalCost'],
                                                      'banner_impressions_30': x['banner_impressions'],
                                                      'banner_clicks_30': x['banner_clicks'],
                                                      'banner_clicksUnique_30': x['banner_clicksUnique'],
                                                      'banner_social_impressions_30': x['banner_social_impressions'],
                                                      'banner_social_clicks_30': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique_30':x['banner_social_clicksUnique'],
                                                      'imp_banner_totalCost_30': x['imp_banner_totalCost'],
                                                      'imp_banner_impressions_30': x['imp_banner_impressions'],
                                                      'imp_banner_clicks_30': x['imp_banner_clicks'],
                                                      'imp_banner_clicksUnique_30': x['imp_banner_clicksUnique'],
                                                      'imp_banner_social_impressions_30': x['imp_banner_social_impressions'],
                                                      'imp_banner_social_clicks_30': x['imp_banner_social_clicks'],
                                                      'imp_banner_social_clicksUnique_30': x['imp_banner_social_clicksUnique']
                                                      }},
                                            upsert=True, safe=True)
            if x['user'] in userStats30:
                userStats30.remove(x['user'])
        for x in userStats30:
            db.stats_user_summary.update({'user': x},
                                              {'$set': {'totalCost_30': 0,
                                                      'teaser_totalCost_30': 0,
                                                      'impressions_30': 0,
                                                      'impressions_block_30': 0,
                                                      'clicks_30': 0,
                                                      'clicksUnique_30': 0,
                                                      'social_impressions_30': 0,
                                                      'social_impressions_block_30': 0,
                                                      'social_clicks_30': 0,
                                                      'social_clicksUnique_30': 0,
                                                      'banner_totalCost_30': 0,
                                                      'banner_impressions_30': 0,
                                                      'banner_clicks_30': 0,
                                                      'banner_clicksUnique_30': 0,
                                                      'banner_social_impressions_30': 0,
                                                      'banner_social_clicks_30': 0,
                                                      'banner_social_clicksUnique_30': 0,
                                                      'imp_banner_totalCost_30': 0,
                                                      'imp_banner_impressions_30': 0,
                                                      'imp_banner_clicks_30': 0,
                                                      'imp_banner_clicksUnique_30': 0,
                                                      'imp_banner_social_impressions_30': 0,
                                                      'imp_banner_social_clicks_30': 0,
                                                      'imp_banner_social_clicksUnique_30': 0
                                                      }},
                                            upsert=True, safe=True)


        for x in cur365:
            db.stats_user_summary.update({'user': x['user']},
                                              {'$set': {'totalCost_365': x['totalCost'],
                                                      'teaser_totalCost_365': x['teaser_totalCost'],
                                                      'impressions_365': x['impressions'],
                                                      'impressions_block_365': x['impressions_block'],
                                                      'clicks_365': x['clicks'],
                                                      'clicksUnique_365': x['clicksUnique'],
                                                      'social_impressions_365': x['social_impressions'],
                                                      'social_impressions_block_365': x['social_impressions_block'],
                                                      'social_clicks_365': x['social_clicks'],
                                                      'social_clicksUnique_365':x['social_clicksUnique'],
                                                      'banner_totalCost_365': x['banner_totalCost'],
                                                      'banner_impressions_365': x['banner_impressions'],
                                                      'banner_clicks_365': x['banner_clicks'],
                                                      'banner_clicksUnique_365': x['banner_clicksUnique'],
                                                      'banner_social_impressions_365': x['banner_social_impressions'],
                                                      'banner_social_clicks_365': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique_365':x['banner_social_clicksUnique'],
                                                      'imp_banner_totalCost_365': x['imp_banner_totalCost'],
                                                      'imp_banner_impressions_365': x['imp_banner_impressions'],
                                                      'imp_banner_clicks_365': x['imp_banner_clicks'],
                                                      'imp_banner_clicksUnique_365': x['imp_banner_clicksUnique'],
                                                      'imp_banner_social_impressions_365': x['imp_banner_social_impressions'],
                                                      'imp_banner_social_clicks_365': x['imp_banner_social_clicks'],
                                                      'imp_banner_social_clicksUnique_365': x['imp_banner_social_clicksUnique']
                                                      }},
                                            upsert=True, safe=True)
            if x['user'] in userStats365:
                userStats365.remove(x['user'])
        for x in userStats365:
            db.stats_user_summary.update({'user': x},
                                              {'$set': {'totalCost_365': 0,
                                                      'teaser_totalCost_365': 0,
                                                      'impressions_365': 0,
                                                      'impressions_block_365': 0,
                                                      'clicks_365': 0,
                                                      'clicksUnique_365': 0,
                                                      'social_impressions_365': 0,
                                                      'social_impressions_block_365': 0,
                                                      'social_clicks_365': 0,
                                                      'social_clicksUnique_365': 0,
                                                      'banner_totalCost_365': 0,
                                                      'banner_impressions_365': 0,
                                                      'banner_clicks_365': 0,
                                                      'banner_clicksUnique_365': 0,
                                                      'banner_social_impressions_365': 0,
                                                      'banner_social_clicks_365': 0,
                                                      'banner_social_clicksUnique_365': 0,
                                                      'imp_banner_totalCost_365': 0,
                                                      'imp_banner_impressions_365': 0,
                                                      'imp_banner_clicks_365': 0,
                                                      'imp_banner_clicksUnique_365': 0,
                                                      'imp_banner_social_impressions_365': 0,
                                                      'imp_banner_social_clicks_365': 0,
                                                      'imp_banner_social_clicksUnique_365': 0
                                                      }},
                                            upsert=True, safe=True)

        # Доход
        inc = {}
        income = db.stats_daily_adv.group(['user'],
                                          {},
                                          {'sum': 0},
                                          'function(o,p) {p.sum += (o.totalCost || 0); }')
        for item in income:
            inc[item.get('user')] = item.get('sum',0.0)
        # Сумма выведенных денег
        outc = {}
        outcome = db.money_out_request.group(['user.login'],
                                          {'approved':True},
                                          {'sum': 0},
                                          'function(o,p) {p.sum += (o.summ || 0); }')
        for item in outcome:
            outc[item.get('user.login')] = item.get('sum',0.0)
        for key, value in inc.items():
            db.stats_user_summary.update({'user': key},
                                              {'$set': {'summ': (float(value) - float(outc.get(key, 0.0)))}},
                                            upsert=False, safe=True)

        registrationDate = {}
        for item in db.users.find({},{'login':1,'registrationDate':1,'_id':0}):
            registrationDate[item.get('login')] = item.get('registrationDate')

        domain_data = {}
        for x in db.stats_daily_adv.find({'date': date}, {'geoClicks': False, 'geoClicksUnique': False, 'geoImpressions': False, 'geoSocialClicks': False, 'geoSocialClicksUnique': False, 'geoSocialImpressions': False}):
            key = (x.get('user'), x.get('domain'))
            data = domain_data.setdefault(key, {'clicks': 0,
                                                 'imps': 0})
            data['clicks'] += x.get('clicks', 0)
            data['imps'] += x.get('impressions', 0)

        domain_activity = {}
        for k, v in domain_data.items():
            user = k[0]
            domain_activity.setdefault(user, 0)
            if v['clicks'] > 0 or v['imps'] >= 100:
                domain_activity[user] += 1
        for item in db.stats_user_summary.find():
            activity = 'orangeflag'
            activity_yesterday = 'orangeflag'
            activity_before_yesterday = 'orangeflag'
            if item.get('impressions_block_2',0)  > 100 :
                activity_yesterday = 'greenflag'
            if item.get('impressions_block_3',0)  > 100 :
                activity_before_yesterday = 'greenflag'
            if item.get('impressions_block',0)  > 100 :
                activity = 'greenflag' 
            if (activity == 'orangeflag') and ((activity_yesterday != 'orangeflag') or (activity_before_yesterday != 'orangeflag')):
                activity = 'redflag'
            item['activity']= activity
            item['activity_yesterday']= activity_yesterday
            item['activity_before_yesterday']= activity_before_yesterday
            item['registrationDate']= registrationDate.get(item['user'])
            item['active_domains'] = {'today': domain_activity.get(item['user'],0),
                                                 'yesterday': 0,
                                                 'before_yesterday': 0}
            db.stats_user_summary.save(item)

        act_acc_count = 0
        domains_today = 0
        users = [x['login'] for x in db.users.find({'accountType': 'user'}).sort('registrationDate')]
        for x in db.stats_user_summary.find():
            '''TODO Почистить базу от Сивоконь вей и убрать эту дуратскую проверку на вхождения пользователя'''
            if x['user'] not in users: continue
            if x['activity'] == 'greenflag':
                act_acc_count += 1 
            domains_today += x.get('active_domains', {}).get('today',0)
        db.stats_daily_all.update({'date': date },
                                        {'$set': {'act_acc_count': act_acc_count,
                                                  'domains_today': domains_today,
                                                  'acc_count':len(users)}},
                                        upsert=False, safe=True)
        current_time = datetime.datetime.today()
        db.config.update({'key': 'last stats_user_summary update'},
                                     {'$set': {'value': current_time}},
                                     upsert=True) 
#            db.stats_user_summary.update({'user': key},
#                                             {'$set': {
#                                             'activity': activity,
#                                             'activity_yesterday': activity_yesterday,
#                                             'activity_before_yesterday': activity_before_yesterday,
#                                             'registrationDate': user['registrationDate'],
#                                             'active_domains':
#                                                {'today': active_domains_today,
#                                                 'yesterday': active_domains_yday,
#                                                 'before_yesterday': active_domains_byday}
#                                            }},
#                                            safe=True,
#                                            upsert=False)

    def createOfferRating(self, db):
        '''-------------------------------'''
        log=logging.getLogger('main') 
        log.setLevel(logging.INFO) 
        formatter=logging.Formatter('%(asctime)s.%(msecs)d %(message)s','%Y-%m-%d %H:%M:%S') 
        dt = datetime.datetime.now()
        log_file = '/var/log/Rating/' + 'OfferRating' + dt.strftime('%Y%m%d') + '.log'
        handler=logging.FileHandler(log_file, 'a') 
        handler.setLevel(logging.INFO) 
        handler.setFormatter(formatter) 
        log.addHandler(handler) 
        log.log(1, 'low level message') 
        log.info("START CREATING OFFER RATTING") 
        '''-------------------------------'''
        offers = db.offer.find()
        offer_count = 0
        offer_skip = 0
        for offer in offers:
            '''
            log.info("/---------------------------------------/")
            log.info("GET OFFER")
            log.info('Title : %s' % offer['title'])
            log.info('Campaign : %s'  %offer['campaignTitle'])
            log.info('GUID : %s' % offer['guid'])
            log.info('Camp GUID : %s' % offer['campaignId'])
            log.info('Rating : %s' % offer['rating'])
            log.info('Uniq : %s' % offer['uniqueHits'])
            log.info('Cost : %s' % offer['cost'])'''
            impressions = offer.get('impressions', 0)
            clicks = offer.get('clicks', 0)
            old_impressions = offer.get('old_impressions', 0)
            old_clicks = offer.get('old_clicks', 0)
            offer_cost = offer.get('cost', 0.1)
            rating_skip = offer.get('skip', 0) + 1
            if (clicks and impressions) > 0 :
                ctr = ((float(clicks)/impressions) * 100)
            else:
                ctr = 0
            if (old_clicks and old_impressions) > 0 :
                border_ctr = ((float(old_clicks)/old_impressions) * 100)
            else:
                border_ctr = 0
            '''log.info('impressions %s' % impressions)
            log.info('clicks %s' % clicks) 
            log.info('old_impressions %s' % old_impressions) 
            log.info('old_clicks %s' % old_clicks) 
            log.info('rating_skip %s' % rating_skip) 
            log.info('offer cost %s' % offer_cost) 
            log.info('ctr %s' % ctr) 
            log.info('border_ctr %s' % border_ctr)'''
            if ctr > 0 :
                '''log.info("CTR > 0")'''
                if ((abs(ctr - border_ctr) >= 0.005) and (impressions > 600)):
                    '''log.info("((abs(ctr - border_ctr) >= 0.005) and (impressions > 2500))")'''
                    offer_count += 1
                    rating = ( ctr * offer_cost) * 100000
                    '''log.info(round(rating, 4))'''
                    db.offer.update({'guid': offer['guid']}, \
                            {'$set': {'rating': round(rating, 4),
                                      'skip': 0, 
                                      'old_impressions': impressions,
                                      'old_clicks': clicks }}, upsert=False, safe=True)
                    MQ().offer_update(offer['guid'], offer['campaignId'])
                else:
                    '''log.info("SKIP")'''
                    offer_skip += 1
                    db.offer.update({'guid': offer['guid']}, \
                            {'$set': {'skip': rating_skip}}, upsert=False, safe=True)
            else:
                '''log.info("CTR < 0")'''
                if (impressions > 600): #and (rating_skip > 3)):
                    '''log.info("(impressions > 2500)")'''
                    offer_count += 1
                    rating = ( ctr * offer_cost) * 100000
                    '''log.info(round(rating, 4))'''
                    db.offer.update({'guid': offer['guid']}, \
                            {'$set': {'rating': round(rating, 4),
                                      'skip': 0, 
                                      'old_impressions': impressions,
                                      'old_clicks': clicks }}, upsert=False, safe=True)
                    MQ().offer_update(offer['guid'], offer['campaignId'])
                else:
                    '''log.info("SKIP")'''
                    offer_skip += 1
                    db.offer.update({'guid': offer['guid']}, \
                            {'$set': {'skip': rating_skip}}, upsert=False, safe=True)
            '''log.info("/---------------------------------------/")'''
        log.info("STOP CREATING OFFER RATTING") 


        print "Created %d rating for offer, skip %d offer" % (offer_count, offer_skip)


    def createOfferRadingForInformers(self, db):
        '''-------------------------------'''
        log=logging.getLogger('main') 
        log.setLevel(logging.INFO) 
        formatter=logging.Formatter('%(asctime)s.%(msecs)d %(message)s','%Y-%m-%d %H:%M:%S') 
        dt = datetime.datetime.now()
        log_file = '/var/log/Rating/' + 'OfferRadingForInformers' + dt.strftime('%Y%m%d') + '.log'
        handler=logging.FileHandler(log_file, 'a') 
        handler.setLevel(logging.INFO) 
        handler.setFormatter(formatter) 
        log.addHandler(handler) 
        log.log(1, 'low level message') 
        log.info("START CREATING OFFER FOR INFORMER RATTING") 
        '''-------------------------------'''
        offers = db.stats_daily.rating.find()
        offer_count = 0
        offer_skip = 0
        costs = {}
        for item in db.offer.find({}, {'guid': True, 'cost': True}):
            costs[item['guid']] = item['cost']

        for offer in offers:
            '''log.info("/---------------------------------------/")
            log.info("GET OFFER")
            log.info('Title : %s' % offer['title'])
            log.info('Campaign : %s'  %offer['campaignTitle'])
            log.info('GUID : %s' % offer['guid'])
            log.info('Camp GUID : %s' % offer['campaignId'])
            log.info('Informer : %s' % offer['adv'])'''
            impressions = offer.get('impressions', 0)
            clicks = offer.get('clicks', 0)
            old_impressions = offer.get('old_impressions', 0)
            old_clicks = offer.get('old_clicks', 0)
            offer_cost = costs.get(offer['guid'], 0.5)
            rating_skip = offer.get('skip', 0) + 1
            if (clicks and impressions) > 0 :
                ctr = ((float(clicks)/impressions) * 100)
            else:
                ctr = 0
            if (old_clicks and old_impressions) > 0 :
                old_ctr = ((float(old_clicks)/old_impressions) * 100)
            else:
                old_ctr = 0
            '''log.info('impressions %s' % impressions)
            log.info('clicks %s' % clicks) 
            log.info('old_impressions %s' % old_impressions) 
            log.info('old_clicks %s' % old_clicks) 
            log.info('rating_skip %s' % rating_skip) 
            log.info('offer cost %s' % offer_cost) 
            log.info('ctr %s' % ctr) 
            log.info('old_ctr %s' % old_ctr) '''
            if ctr > 0 :
                '''log.info("CTR > 0")'''
                if ((abs(ctr - old_ctr) >= 0.005) and (impressions > 600)):
                    '''log.info("((abs(ctr - border_ctr) >= 0.005) and (impressions > 2500))")'''
                    offer_count += 1
                    rating = (ctr * offer_cost) * 100000
                    '''log.info(round(rating, 4))'''
                    db.stats_daily.rating.update({'guid': offer['guid'],
                                                  'campaignId': offer['campaignId'],
                                                  'campaignTitle': offer['campaignTitle'],
                                                  'title': offer['title'],
                                                  'adv':offer['adv']}, 
                                                  {'$set': {'rating': round(rating, 4),
                                                  'cost': offer_cost,
                                                  'skip': 0,
                                                  'old_impressions': impressions,
                                                  'old_clicks': clicks }}, upsert=False, safe=True)
                else:
                    '''log.info("SKIP")'''
                    offer_skip += 1
                    db.stats_daily.rating.update({'guid': offer['guid'],
                                                  'campaignId': offer['campaignId'],
                                                  'campaignTitle': offer['campaignTitle'],
                                                  'title': offer['title'],
                                                  'adv':offer['adv']}, 
                                                  {'$set': {'skip': rating_skip}}, upsert=False, safe=True)
            else:
                '''log.info("CTR < 0")'''
                if (impressions > 600): # and (rating_skip > 3)):
                    '''log.info("(impressions > 2500)")'''
                    offer_count += 1
                    rating = (ctr * offer_cost) * 100000
                    '''log.info(round(rating, 4))'''
                    db.stats_daily.rating.update({'guid': offer['guid'],
                                                  'campaignId': offer['campaignId'],
                                                  'campaignTitle': offer['campaignTitle'],
                                                  'title': offer['title'],
                                                  'adv':offer['adv']}, 
                                                  {'$set': {'rating': round(rating, 4),
                                                  'cost': offer_cost,
                                                  'skip': 0,
                                                  'old_impressions': impressions,
                                                  'old_clicks': clicks }}, upsert=False, safe=True)
                else:
                    '''log.info("SKIP")'''
                    offer_skip += 1
                    db.stats_daily.rating.update({'guid': offer['guid'],
                                                  'campaignId': offer['campaignId'],
                                                  'campaignTitle': offer['campaignTitle'],
                                                  'title': offer['title'],
                                                  'adv':offer['adv']}, 
                                                  {'$set': {'skip': rating_skip}}, upsert=False, safe=True)
            '''log.info("/---------------------------------------/")'''
        log.info("STOP CREATING OFFER FOR INFORMER RATTING") 
        print "Created %d rating for offer-informer, skip %d offer-informer" % (offer_count, offer_skip)

    def updateWorkerRadingForInformers(self, db):
        '''-------------------------------'''
        log=logging.getLogger('main') 
        log.setLevel(logging.INFO) 
        formatter=logging.Formatter('%(asctime)s.%(msecs)d %(message)s','%Y-%m-%d %H:%M:%S') 
        dt = datetime.datetime.now()
        log_file = '/var/log/Rating/' + 'UpdateWorkerRadingForInformers' + dt.strftime('%Y%m%d') + '.log'
        handler=logging.FileHandler(log_file, 'a') 
        handler.setLevel(logging.INFO) 
        handler.setFormatter(formatter) 
        log.addHandler(handler) 
        log.log(1, 'low level message') 
        log.info("START UPDATE WORKER OFFER FOR INFORMER RATTING") 
        '''-------------------------------'''
        log.info('START GROUP')                                                                                                                                                                                                                                                                                                                            
        informers = db.stats_daily.rating.group(
                    key = ['adv'],
                    condition = {'rating': {'$exists': True}},
                    reduce = '''function(o, p) {p.rating[o.guid] = o.rating;}''',
                    initial = {'rating' : {}}
                    )
        log.info('STOP GROUP')                                                                                                                                                                                                                                                                                                                            
        for x in informers:
            '''log.info('Informer : %s' % x['adv'])
            log.info('Rating : %s' % x['rating'])'''
            db.informer.rating.update({'guid': x['adv']},
                                      {'$set': {'rating': x['rating']}},
                                      upsert=True, safe=True)
            MQ().rating_informer_update(x['adv'])
        log.info("STOP UPDATE WORKER OFFER FOR INFORMER RATTING") 
        print 'Update worker rating to %s informers' % len(informers)


    def count_AccountsDomains_overall_by_date(self, db, date):
        u"""Просчитывает кол-во активных аккаунтов и сайтов по предприятию с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date"""
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        act_acc_count = 0
        domains_today = 0
        users = [x['login'] for x in db.users.find({'accountType': 'user'}).sort('registrationDate')]
        for x in db.user.summary_per_date.find():
            '''TODO Почистить базу от Сивоконь вей и убрать эту дуратскую проверку на вхождения пользователя'''
            if x['login'] not in users: continue
            if x['activity'] == 'greenflag':
                act_acc_count += 1 
            active_domains = x.get('active_domains', {})
            domains_today += active_domains.get('today', 0)
        db.stats_overall_by_date.update({'date': date },
                                        {'$set': {'act_acc_count': act_acc_count,
                                                  'domains_today': domains_today,
                                                  'acc_count':len(users)}},
                                        upsert=True)
    
    
    def agregate_overall_by_date(self, db, date):
        u"""Составляет общую статистику по предприятию с разбивкой по датам.
            Данные используються в менеджеровском акаунте для обшей статистики
            ``date`` --- дата, на которую считать данные. Может быть типа datetime или date"""
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        summary = db.stats_daily_adv.group(
            key = ['date'],
            condition = {'date': {'$gte': date,
                                  '$lt': date + datetime.timedelta(days=1)}},
            reduce = '''
                function(o, p) {
                   p.clicks += o.clicks || 0;
                   p.view_seconds += o.view_seconds || 0;
                   p.clicksUnique += o.clicksUnique || 0;
                   p.banner_clicks += o.banner_clicks || 0;
                   p.banner_clicksUnique += o.banner_clicksUnique || 0;
                   p.impressions += o.impressions || 0;
                   p.social_impressions += o.social_impressions || 0;
                   p.impressions_block += o.impressions_block || 0;
                   p.social_impressions_block += o.social_impressions_block || 0;
                   p.social_clicks += o.social_clicks || 0;
                   p.social_clicksUnique += o.social_clicksUnique || 0;
                   p.banner_social_clicks += o.banner_social_clicks || 0;
                   p.banner_social_clicksUnique += o.banner_social_clicksUnique || 0;
                   p.totalCost += o.totalCost || 0;
                   p.manyClicks += o.manyClicks || 0;
                   p.badTokenIp += o.badTokenIp || 0;
                   p.blacklistIp += o.blacklistIp || 0;

                   var dataGeoImpressions = o.geoImpressions;
                   for (var key in dataGeoImpressions) {
                       var country = key;
                       var city_ar = dataGeoImpressions[country][1];
                       if (p.geoImpressions[country] == undefined){
                           p.geoImpressions[country] = [0,{}];
                           p.geoImpressions[country][0] = dataGeoImpressions[country][0];
                       }else{
                           p.geoImpressions[country][0] += dataGeoImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoImpressions[country][1][key] == undefined){
                               p.geoImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialImpressions = o.geoSocialImpressions;
                   for (var key in dataGeoSocialImpressions) {
                       var country = key;
                       var city_ar = dataGeoSocialImpressions[country][1];
                       if (p.geoSocialImpressions[country] == undefined){
                           p.geoSocialImpressions[country] = [0,{}];
                           p.geoSocialImpressions[country][0] = dataGeoSocialImpressions[country][0];
                       }else{
                           p.geoSocialImpressions[country][0] += dataGeoSocialImpressions[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialImpressions[country][1][key] == undefined){
                               p.geoSocialImpressions[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialImpressions[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicks = o.geoClicks;
                   for (var key in dataGeoClicks) {
                       var country = key;
                       var city_ar = dataGeoClicks[country][1];
                       if (p.geoClicks[country] == undefined){
                           p.geoClicks[country] = [0,{}];
                           p.geoClicks[country][0] = dataGeoClicks[country][0];
                       }else{
                           p.geoClicks[country][0] += dataGeoClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicks[country][1][key] == undefined){
                               p.geoClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicks = o.geoSocialClicks;
                   for (var key in dataGeoSocialClicks) {
                       var country = key;
                       var city_ar = dataGeoSocialClicks[country][1];
                       if (p.geoSocialClicks[country] == undefined){
                           p.geoSocialClicks[country] = [0,{}];
                           p.geoSocialClicks[country][0] = dataGeoSocialClicks[country][0];
                       }else{
                           p.geoSocialClicks[country][0] += dataGeoSocialClicks[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicks[country][1][key] == undefined){
                               p.geoSocialClicks[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicks[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoClicksUnique = o.geoClicksUnique;
                   for (var key in dataGeoClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoClicksUnique[country][1];
                       if (p.geoClicksUnique[country] == undefined){
                           p.geoClicksUnique[country] = [0,{}];
                           p.geoClicksUnique[country][0] = dataGeoClicksUnique[country][0];
                       }else{
                           p.geoClicksUnique[country][0] += dataGeoClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoClicksUnique[country][1][key] == undefined){
                               p.geoClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }


                   var dataGeoSocialClicksUnique = o.geoSocialClicksUnique;
                   for (var key in dataGeoSocialClicksUnique) {
                       var country = key;
                       var city_ar = dataGeoSocialClicksUnique[country][1];
                       if (p.geoSocialClicksUnique[country] == undefined){
                           p.geoSocialClicksUnique[country] = [0,{}];
                           p.geoSocialClicksUnique[country][0] = dataGeoSocialClicksUnique[country][0];
                       }else{
                           p.geoSocialClicksUnique[country][0] += dataGeoSocialClicksUnique[country][0];
                       }
                       for (var key in city_ar){
                           if (p.geoSocialClicksUnique[country][1][key] == undefined){
                               p.geoSocialClicksUnique[country][1][key] = city_ar[key];
                           }
                           else{
                               p.geoSocialClicksUnique[country][1][key] += city_ar[key];
                           }
                       }
                   }
                }''',
                initial = {'clicks': 0,
                           'clicksUnique': 0,
                           'banner_clicks':0,
                           'banner_clicksUnique':0,
                           'impressions': 0,
                           'social_impressions': 0,
                           'impressions_block': 0,
                           'social_impressions_block': 0,
                           'social_clicks': 0,
                           'social_clicksUnique': 0,
                           'banner_social_clicks':0,
                           'banner_social_clicksUnique':0,
                           'totalCost': 0,
                           'badTokenIp': 0,
                           'blacklistIp': 0, 
                           'manyClicks': 0,
                           'geoImpressions': {},
                           'geoSocialImpressions': {},
                           'geoClicks':{},
                           'geoSocialClicks':{},
                           'geoClicksUnique':{},
                           'geoSocialClicksUnique':{},
                           'view_seconds':0
                           }
        )
        for x in summary:
            db.stats_overall_by_date.update({'date': x['date']},
                                            {'$set': {'clicks': x['clicks'],
                                                      'clicksUnique': x['clicksUnique'],
                                                      'banner_clicks': x['banner_clicks'],
                                                      'banner_clicksUnique': x['banner_clicksUnique'],
                                                      'impressions': x['impressions'],
                                                      'social_impressions': x['social_impressions'],
                                                      'impressions_block': x['impressions_block'],
                                                      'social_impressions_block': x['social_impressions_block'],
                                                      'social_clicks': x['social_clicks'],
                                                      'social_clicksUnique':x['social_clicksUnique'],
                                                      'banner_social_clicks': x['banner_social_clicks'],
                                                      'banner_social_clicksUnique':x['banner_social_clicksUnique'],
                                                      'totalCost': x['totalCost'],
                                                      'blacklistIp': x['blacklistIp'],
                                                      'badTokenIp': x['badTokenIp'],
                                                      'manyClicks': x['manyClicks'],
                                                      'geoImpressions': x['geoImpressions'],
                                                      'geoSocialImpressions': x['geoSocialImpressions'],
                                                      'geoClicks': x['geoClicks'],
                                                      'geoSocialClicks': x['geoSocialClicks'],
                                                      'geoClicksUnique': x['geoClicksUnique'],
                                                      'geoSocialClicksUnique': x['geoSocialClicksUnique'],
                                                      'view_seconds':x['view_seconds']
                                                      }},
                                            upsert=True, safe=True)


    def agregateBannerStatsDailyAdv(self, db, date):
        assert isinstance(date, (datetime.datetime, datetime.date))
        date2 = (datetime.date.today() - datetime.timedelta(days=1))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        date2 = datetime.datetime(date2.year, date2.month, date2.day, 0, 0)
        print date
        impresionCost = {}
        userCost = {}
        blockCost = {}
        for item in db.banner.offer.find({},{'imp_cost':1,'guid':1,'_id':0}):
            impresionCost[item['guid']] = float(item['imp_cost'])/1000
        for item in db.users.find({'cost':{'$exists': True}},{'login':1,'cost':1}):
            userCost[item['login']] = item['cost']
        for item in db.informer.find({},{'guid':1,'cost':1,'user':1}):
            blockCost[item['guid']] = {'login':item['user'], 'cost': item.get('cost', None)}
        def _partner_cost(informer_id, cost, imp):
            ''' Возвращает цену для сайта-партнёра.
                ``informer_id``
                    ID информера, по которому произошёл клик.
                ``cost``
                    Цена рекламодателя.
            '''
            block_Cost = blockCost[informer_id]['cost'] if (blockCost[informer_id]['cost'] != None) else userCost[blockCost[informer_id]['login']]
            percent = int(block_Cost.get('ALL',{}).get('imp',{}).get('percent',50))
            cost_min = float(block_Cost.get('ALL',{}).get('imp',{}).get('cost_min',  0.01)) / 1000
            cost_max = float(block_Cost.get('ALL',{}).get('imp',{}).get('cost_max', 1.00)) / 1000
            cost = cost * percent / 100
            cost_min = cost_min * imp
            cost_max = cost_max * imp
            if cost_min and cost < cost_min:
                cost = cost_min
            if cost_max and cost > cost_max:
                cost = cost_max
            return cost

        bannerStats = db.banner.stats_daily.find({'date':date, 'banner_impressions': { '$exists': True }})
        for item in bannerStats:
            cost = item['banner_impressions'] * impresionCost[item['guid']]
            item['cost'] = cost
            item['block_cost'] = _partner_cost(item['adv'], cost, item['banner_impressions'])
            db.banner.stats_daily.save(item)
            if date == date2:
                db.banner.offer.update({'guid':item['guid']}, {'$inc': {'budget': -cost}}, upsert=False, safe=True)
        groupBannerStats = db.banner.stats_daily.group(
            key = ['adv','date'],
            condition = {'date': date, 'block_cost': { '$exists': True }},
            reduce = '''
                function(o, p) {
                p.cost += o.block_cost;
                }''',
                initial = {'cost': 0 })
        for item in groupBannerStats:
            db.stats_daily_adv.update(
                    {'adv': item['adv'], 'date': item['date'], 'isOnClick': False},
                    {'$set': {'totalCost': item['cost']}},
                        upsert=True, safe=True)

    def createCatigoriesDomainReport(self, db, date):
        assert isinstance(date, (datetime.datetime, datetime.date))
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        print date
        activ_domain = [ item['domain'] for item in db.stats_daily_domain.find({'date':date, 'impressions_block':{'$gte':100}},{'domain':1,'_id':0})]
        all_domain = []
        for item in db.user.domains.find():
            for x in item['domains']:
                all_domain.append(x)
        category = {}
        cur = db.advertise.category.find()
        for item in cur:
            value = {'activ':[],'notActiv':[]}
            domain = db.domain.categories.find({"categories": item['guid']})
            for i in domain:
                if i['domain'] in activ_domain:
                    value['activ'].append(i['domain'])
                else:
                    value['notActiv'].append(i['domain'])
                if i['domain'] in all_domain:
                    all_domain.remove(i['domain'])
            category[item['title']] = value
        font0 = xlwt.Font()
        font0.name = 'Times New Roman'
        font0.colour_index = 0
        font0.height = 360
        font0.bold = True
        style0 = xlwt.XFStyle()
        style0.font = font0

        font1 = xlwt.Font()
        font1.name = 'Times New Roman'
        font1.colour_index = 0
        font1.height = 280
        font1.bold = False
        style1 = xlwt.XFStyle()
        style1.font = font1

        wbk = xlwt.Workbook('utf-8')
        sheet = wbk.add_sheet('Рубрикатор')
        sheet.write(0, 0, 'Категория',style0)
        sheet.write(0, 1, 'Активный',style0)
        sheet.write(0, 2, 'Не активный',style0)
        sheet.col(0).width = 256 * 50
        sheet.col(1).width = 256 * 50
        sheet.col(2).width = 256 * 50
        count = 1
        for key,value in category.items():
            sheet.write(count,0,key,style1)
            for idx, val in enumerate(value['activ']):
                sheet.write(count+idx,1,val,style1)
            for idx, val in enumerate(value['notActiv']):
                sheet.write(count+idx,2,val,style1)
            if (len(value['activ']) >= len(value['notActiv'])):
                count += len(value['activ'])
            else:
                count += len(value['notActiv'])
            sheet.write_merge(count,count,0,2,'',style1)
            count += 1
        sheet1 = wbk.add_sheet('Неназначеные')
        sheet1.col(0).width = 256 * 50
        for idx, val in enumerate(all_domain):
             sheet1.write(idx,0,val,style1)
        buf = StringIO.StringIO()
        wbk.save(buf)
        buf.seek(0)
        ftp = ftplib.FTP(host='213.186.121.76')
        ftp.login('cdn', '$www-app$')
        ftp.cwd('getmyad')
        ftp.cwd('report')
        ftp.storbinary('STOR category_report.xls', buf)
        ftp.close()

