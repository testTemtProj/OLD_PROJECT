# coding: utf-8
import sys
sys.path.append('.')

import celery
from celery.task import task, periodic_task 
from celery.task.schedules import crontab
from celery.events.state import State
from celery.task.base import Task

from datetime import datetime

import pymongo

from xmlrpclib import ServerProxy

import ConfigParser
import os

PYLONS_CONFIG = "deploy.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config_parser = ConfigParser.ConfigParser()
config_parser.read(config_file)

from multidownload import Parser

ADLOAD_RPC = config_parser.get('app:main', 'WSDL_ADLOAD')
MONGO_HOST = config_parser.get('app:main', 'mongo_host')
con = pymongo.Connection(MONGO_HOST)
db = con[config_parser.get('app:main', 'mongo_database')]

from parseryml.model.marketModel import MarketModel

DAYS_OF_WEEK = {'понедельник':  0,
                'вторник':      1,
                'среда':        2,
                'четверг':      3,
                'пятница':      4,
                'суббота':      5,
                'воскресенье':  6,
                None:           -1}

#@periodic_task(run_every=crontab(minute="*/60"))
#def parse_every():
#    """Выполнения парсинга, выполняется каждые 60 минут"""
#    #return    
#    for market in db.toParse.find():        
#        parse_by_id.delay(market['id'])
#        db.toParse.remove(market)    
            
@periodic_task(run_every=crontab(minute="*/60"))
def parse_every_time():
    """Выполнения парсинга магазина, выполняется каждые 10 минут"""     
    time = datetime.now()
    
    for market in db.toParse.find():        
        h = int(market['time'].split(":")[0])
        m = int(market['time'].split(":")[1])        
        if time.hour <= h and h < time.hour + 1:# and time.minute<m<time.minute+10:
            #parse_by_id.delay(market['id'])
            parse_by_id.apply_async(args=[market['id']], queue="parse_yml_task", routing_key="parseryml.process")
            db.toParse.remove(market)              


@periodic_task(run_every=crontab(hour=0, minute=[0], day_of_week=[0, 1, 2, 3, 4, 5, 6, ]))
def check_all_advertise():
    """
    Задача проверяет какие магазины нужно парсит и составляет расписания задач на сутки 
    """    
    current_date = datetime.now()
    res = []    
    for r in db.Market.find():          
        del(r['_id'])
        res.append(r) 
    db.toParse.remove()     
    for market in res:        
        if market.has_key('time_setting'):                        
            try:            
                if market['time_setting']['interval'] == u"час":
                    
                    for hour in xrange(0,23):
                        db.toParse.insert({'id':market['id'], 'time':"%s:00" % hour})
                          
                if market['time_setting']['interval'] == u"день":
                    
                    for time in market['time_setting']['Params']:
                        if isinstance(time, dict):                        
                            db.toParse.insert({'id':market['id'], 'time':time.get('time', '00:00')})
                                               
                elif market['time_setting']['interval'] == u"неделю":
                    
                    for time in market['time_setting']['Params']:
                        
                        if current_date.weekday()==DAYS_OF_WEEK[time.get('dayOfWeak', None)]:
                            db.toParse.insert({'id':market['id'], 'time':time['time']})                      
                
                elif market['time_setting']['interval'] == u"месяц":
                    
                    for time in market['time_setting']['Params']:
                        if current_date.day == time.get('day', -1):
                            db.toParse.insert({'id':market['id'], 'time':time['time']})
                    
                elif market['time_setting']['interval'] == u"год":
                    for time in market['time_setting']['Params']:
                        day = time['date']['day']
                        month = time['date']['month']
                        if current_date.month == month and current_date.day == day:
                            db.toParse.insert({'id':market['id'], 'time':time['time']})                            
                            
            except Exception, ex:
                print ex

                
        elif market.has_key('dateCreate') and market.has_key('last_update'):
            try:                
                time = str(market['last_update'].hour) + ":" + str(market['last_update'].minute)
                db.toParse.insert({'id':market['id'], 'time':time})
            except Exception, ex:
                print ex


@task(name='parse_by_id')
def parse_by_id(id):
    print "Trying to parse market with id %s" % id
    markets_model = MarketModel()
    market = markets_model.get_by_id(id)
    if market:
        if 'taskId' in market:
            task_id = market['taskId']
            parse_task = Task().AsyncResult(task_id)
            if parse_task.state in ('STARTED'):
                print "Market with id %s handles by other worker" % id 
                return {'ok':False}

        print "Start parsing market by id: %s" %(id)
        market['taskId'] = parse_by_id.request.id
        markets_model.save(market)

        try:
            parser = Parser()
            parser.parse_by_id(int(id))
            #parse_by_id.update_state(state="SUCCESS", meta={"id": id})
        except Exception, ex:
            print ex
        finally:
            try:
                adload_rpc = ServerProxy(ADLOAD_RPC)
                adload_rpc.update_advertise_by_shop_id(str(id))
            except Exception as message:
                market.set_state_error(id, 501)


@task
def parse_by_url(url, shop_id=None):
    """Задача парсинга магазина по урлу"""
    parser = Parser()
    return parser.parse_by_url(url, shop_id)


@task
def get_category(db, id):
    """Задача получение категорий"""
    cat=[]
    parser = Parser()    
    parser.parse_by_id(int(id))    
    cat = db.Market.find_one({"id":id})['Categories']
    return cat

     
@task 
def market_test_task(url):
    """
    Задача проверки файла выгрузки магазина
    """
    return Parser().test(url=url, is_file=False)
    return "ok"
