# coding: utf-8
from pprint import pprint
from time import sleep
from celery.task import task, periodic_task
from celery.task.schedules import crontab
from campaign_offers_parser import CampaignOffersParser 
from celery.events.state import State 
import os
import ConfigParser

PYLONS_CONFIG = "development.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)

config_for_task = ConfigParser.ConfigParser()
config_for_task.read(config_file)
#LOG = logging.getLogger(__name__)
ADLOAD_XMLRPC_HOST = config_for_task.get('app:main', 'adload_xmlrpc_server')
import xmlrpclib
import pymongo
MONGO_CONN = pymongo.Connection(config_for_task.get('app:main', 'mongo_host'))#"10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019")
MONGO_DB = MONGO_CONN[config_for_task.get('app:main', 'mongo_database')]
ADVERTISE = MONGO_CONN[config_for_task.get('app:main', 'mongo_database')].Advertise

#TODO 10 минут
@periodic_task(run_every=crontab(minute="*/10"), ignore_result=True)
def check_status_in_adload():
    """
        Переодическая задача проверки статуса рекламной кампании в адлоаде
        Выполняется каждые 10 минут
    """
    adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)
    
    try:
        advertise_list = adload.advertise_list()
    except Exception:
        advertise_list = []

    for adload_campaign in advertise_list:
        campaign_collection = ADVERTISE
        rynok_campaign = campaign_collection.find_one({'idAdvertise':adload_campaign['id']})
        
        approved = False
        state = {'status': "stopped", "message": "campaign stopped", "started": None, "finished" : None}
        
        if rynok_campaign:
            if rynok_campaign and 'approved' in rynok_campaign and rynok_campaign['approved']:
                approved = rynok_campaign['approved']

            if 'state' in rynok_campaign and rynok_campaign['state']:
                state = rynok_campaign['state']

        campaign_collection.update({'idAdvertise':adload_campaign['id']}, \
                  {'$set':{'idAdvertise':adload_campaign['id'], \
                           'title': adload_campaign['title'], \
                           'user': adload_campaign['login'], \
                           'state_Adload': adload_campaign['state'], \
                           'approved': approved, \
                           'state': state}}, \
                           upsert=True)
        if (adload_campaign['state'] == False and approved and state['status'] == 'started') or (not approved and state['status'] == 'started'):
            stop_campaign(adload_campaign['id'])


@task(name="start_campaign")
def start_campaign(campaign_id, **kwargs):
    campaign_offers_parser = CampaignOffersParser(campaign_id=campaign_id)
    try:
        return campaign_offers_parser.add_products() 
    #TODO вписать список возможных исключений
    except Exception as exc:
        campaign_offers_parser._set_status_message(status='stopped', message='Campaign stopped')
        campaign_offers_parser.remove_products()


@task(name="update_campaign")
def update_campaign(campaign_id):
    campaign_offers_parser = CampaignOffersParser(campaign_id=campaign_id)
    try:
        return campaign_offers_parser.update_products()
    #TODO вписать список возможных исключений
    except Exception as ex:
        campaign_offers_parser._set_status_message(status='stopped', message='Campaign stopped')
        campaign_offers_parser.remove_products()
    
     
@task(name="stop_campaign", max_retries=3)
def stop_campaign(campaign_id):
    campaign_offers_parser = CampaignOffersParser(campaign_id=campaign_id)
    try:
        return campaign_offers_parser.remove_products()
    #TODO вписать список возможных исключений
    except Exception as exc:
        stop_campaign.retry(exc=exc, countdown=30)
        

               


def inc_popularity_category(category_id):
    """рекурсивный инкремент популярности категории"""
    
    categories = MONGO_DB.Category        
    category = categories.find_one({'ID':category_id})
    
    if category is None:
        return
    
    if category.has_key('popularity'):
        category['popularity'] += 1
    else:
        category['popularity'] = 1
        
    categories.save(category)
    parent_id = category['ParentID']
    
    if parent_id == 0:
        return
     
    inc_popularity_category(category['ParentID'])
        
@periodic_task(run_every=crontab(minute="*/30"), ignore_result=True)
def recount_popularity():
    
    """
        Функция для подсчета популярности товара, категории,
        производитеоя, магазина.
    """
    
    db = MONGO_DB
        
    for counter in [0,1,2]:
        if counter == 0:
            collection = db.clicks
        elif counter == 1:
            collection = db.clicks.error
        elif counter == 2:
            collection = db.clicks.rejected

        for click in collection.find({'ch': {'$exists': False}}):
                        
            click['ch'] = True
            collection.save(click)
            if 'offer' in click:
                try:
                    db.Products.update({'id': click['offer']},{ '$inc' : { 'popularity' : 1 } })
                except:
                    db.Products.update({'id': click['offer']},{'$set':{'popularity': 1}})

            if 'vendor' in click:
                try:
                    db.Vendors.update({'id': click['vendor']},{ '$inc' : { 'popularity' : 1 } })
                except:
                    db.Vendors.update({'id': click['vendor']},{'$set': {'popularity': 1}})
                    
            if 'shopId' in click:
                try:
                    db.Market.update({'id': click['shopId']}, { '$inc' : { 'popularity' : 1 } })
                except:
                    db.Market.update({'id': click['shopId']}, {'$set': {'popularity': 1}})
            
            if 'categoryId' in click:
                inc_popularity_category(click['categoryId'])                


