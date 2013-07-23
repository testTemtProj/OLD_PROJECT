# encoding: utf-8
from pymongo import Connection, DESCENDING
import logging, logging.handlers, sys, os 
import datetime
import pymongo

class GetmyadClean():

    def clean_ip_blacklist(self, db):
        u"""Удаляет старые записи из чёрного списка"""
        db.blacklist.ip.remove({'dt': {'$lte': datetime.datetime.now() - datetime.timedelta(weeks=2)}})


    def decline_unconfirmed_moneyout_requests(self, db):
        u"""Отклоняет заявки, которые пользователи не подтвердили в течении трёх
            дней"""
        clean_to_date = datetime.datetime.now() - datetime.timedelta(days=3)
        print 'Decline unconfirmed %s' % clean_to_date
        db.money_out_request.remove(
                        {'user_confirmed': {'$ne' : True},
                         'approved': {'$ne': True},
                         'date': {'$lte': clean_to_date}}, safe=True)


    def delete_old_stats(self, db):
        u"""Удаляем старую статистику"""
        delete_to_date = datetime.datetime.now() - datetime.timedelta(days=3)
        i = 0
        for x in db.stats_daily.find({'date': {'$lt': delete_to_date}}):
            db.stats_daily.remove(x)
            i += 1
        print "%d records deleted" % i

    def delete_old_rating_stats(self, db):
        u"""Удаляем старую статистику"""
        '''-------------------------------'''
        log=logging.getLogger('main') 
        log.setLevel(logging.INFO) 
        formatter=logging.Formatter('%(asctime)s.%(msecs)d %(message)s','%Y-%m-%d %H:%M:%S') 
        dt = datetime.datetime.now()
        log_file = '/var/log/Rating/' + 'DeleteRadingForInformers' + dt.strftime('%Y%m%d') + '.log'
        handler=logging.FileHandler(log_file, 'a') 
        handler.setLevel(logging.INFO) 
        handler.setFormatter(formatter) 
        log.addHandler(handler) 
        log.log(1, 'low level message') 
        log.info("START DELETE OFFER FOR INFORMER RATTING") 
        '''-------------------------------'''
        offersId = db.offer.group(key={'guid':True}, condition={'hash': {'$exists': True}}, reduce='function(obj,prev){}', initial={})
        offersId = map(lambda x: x['guid'], offersId)
        i = 0
        y = 0
        z = 0
        log.info('DELETE OFFER/INF OLD')
        for x in db.stats_daily.rating.find():
            if x['guid'] not in offersId:
                log.info('Delete : %s' % x)
                db.stats_daily.rating.remove(x)
                i += 1
        log.info('Delete rows %s' % i)
        #Сбрасуем показы и клики в товарах
        log.info('CLEARN OFFER IMP/CLICK')
        for offer in db.offer.find():
            impressions = offer.get('impressions', 0)
            if (impressions > 2500):  
                db.offer.update({'guid': offer['guid']}, \
                                {'$set': {'impressions': 0,
                                          'clicks': 0 }}, safe=True)
                y += 1
        log.info('Clean rows %s' % y)
        #Сбрасуем показы и клики в товарах по рекламному блоку
        log.info('CLEARN OFFER/INF IMP/CLICK')
        for offer in db.stats_daily.rating.find():
            impressions = offer.get('impressions', 0)
            if (impressions > 2500):  
                db.stats_daily.rating.update({'guid': offer['guid'],
                                              'campaignId': offer['campaignId'],
                                              'campaignTitle': offer['campaignTitle'],
                                              'title': offer['title'],
                                              'adv': offer['adv']}, \
                                            {'$set': {'impressions': 0,
                                             'clicks': 0 }}, safe=True)
                z += 1
        log.info('Clean rows %s' % z)
        log.info("STOP DELETE OFFER FOR INFORMER RATTING") 
        print "%d records deleted, clearn offer imp/click %d, clearn offer/inf imp/click %d " % (i, y, z)

    def delete_click_rejected(self, db):
        u"""Удаляем старую статистику по отклонённым кликам"""
        delete_to_date = datetime.datetime.now() - datetime.timedelta(days=4)
        i = 0
        for x in db.clicks.rejected.find({'dt': {'$lt': delete_to_date}}):
            db.clicks.rejected.remove(x)
            i += 1
        print "%d records deleted" % i
