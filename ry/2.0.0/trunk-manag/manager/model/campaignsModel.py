# coding: utf-8
import re
from pprint import pprint
import xmlrpclib

from pylons import config
from trans import trans

from manager.lib import tasks
from manager.model.baseModel import Base 
from manager.model.marketsModel import MarketsModel

from celery.result import AsyncResult

ADLOAD_XMLRPC_HOST = config.get('adload_xmlrpc_server')

class CampaignsModel ():
    
    campaign_collection = Base.campaign_collection
    adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)

    @staticmethod
    def get_all(skip, limit, by, direction, search_pattern, filters):
        query = {'$or' : [
                {'title' : {'$regex':search_pattern, '$options': 'i'}},
                {'user' : {'$regex':search_pattern, '$options': 'i'}}
            ]}
        for column in filters:
            if isinstance(column['value'], bool):
                query[column['field']] = column['value']
                continue

            query[column['field']] = {'$regex': column['value'], '$options': 'i'}
        count = CampaignsModel.campaign_collection.find(query).count()

        return {'result': CampaignsModel.campaign_collection.find(query).sort(by, direction).skip(int(skip)).limit(int(limit)),'count':count} 


    @staticmethod
    def remove(advertise_id):
        CampaignsModel.campaign_collection.remove({'id': advertise_id})
    

    @staticmethod
    def get_count():
        return CampaignsModel.campaign_collection.count()
    

    @staticmethod
    def get_by_id(campaign_id):
        return CampaignsModel.campaign_collection.find_one({'idAdvertise': campaign_id})
    

    @staticmethod
    def start_campaign(campaign_id):
        campaign = CampaignsModel.campaign_collection.find_one({'idAdvertise':campaign_id})
        if campaign is None:
            return {'status': 'error', 'message': 'campaign with id "' + str(campaign_id) + '" not found'}

        if not ('state_Adload' and 'approved') in campaign:
            return {'status': 'error', 'message': 'in the campaign with id "' + str(campaign_id) + '" missing some critical fields'} 

        if not campaign['approved'] or not campaign['state_Adload']:
            return {'status': 'rejected', 'message': 'campaign with id "' + str(campaign_id) + '" is not approved or it is not running in AdLoad'}

        task = tasks.start_campaign.delay(campaign_id) 
        #campaign['task_id'] = task.task_id 
        #CampaignsModel.campaign_collection.save(campaign)
        

    
    @staticmethod
    def stop_campaign(campaign_id):
        campaign = CampaignsModel.campaign_collection.find_one({'idAdvertise':campaign_id})
        if not campaign:
            return {"status": 'error', "msg": 'campaign with id "' + str(campaign_id) + '" not found'}

        task = tasks.stop_campaign.delay(campaign_id)
        #campaign['task_id'] = task.task_id 
        #CampaignsModel.campaign_collection.save(campaign)


    @staticmethod
    def update_campaign(campaign_id):
        campaign = CampaignsModel.campaign_collection.find_one({'idAdvertise':campaign_id})
        if not campaign:
            return {"status": 'error', "msg":' campaign with id "' + str(campaign_id) + '" not found'}

        task = tasks.update_campaign.delay(campaign_id)
        #campaign['task_id'] = task.task_id 
        #CampaignsModel.campaign_collection.save(campaign)

        
    @staticmethod
    def insert(data):
        #TODO сделать валидацию
        CampaignsModel.campaign_collection.update({'idAdvertise':data['id']},{'$set':{'idAdvertise':data['id'], 'title': data['title'], 'user': data['login'], 'state_Adload': data['state']}}, upsert = True)
    
    
    @staticmethod
    def approve_campaign(campaign_id):
        CampaignsModel.campaign_collection.update({'idAdvertise':campaign_id}, {'$set':{'approved':True}})
        CampaignsModel.update_markets_in_campaign(campaign_id)


    @staticmethod
    def prohibit_campaign(campaign_id):
        CampaignsModel.adload.campaign_remove(campaign_id)
        CampaignsModel.campaign_collection.update({'idAdvertise':campaign_id}, {'$set':{'approved':False}})
        CampaignsModel.stop_campaign(campaign_id)

    
    @staticmethod
    def get_in_range(ids):
        return CampaignsModel.campaign_collection.find({'idAdvertise': {'$in':ids}})


    @staticmethod
    def update_markets_in_campaign(campaign_id):
        markets_model = MarketsModel()
        markets_by_campaign = CampaignsModel.adload.get_shops_by_advertise(campaign_id)
        for market in markets_by_campaign:
            market['count'] = 0
            transformed_title = unicode(market['transformedTitle']) if 'transformedTitle' in market else False            
            if not transformed_title:
                title = market['title'] if 'title' in market else ''
                transformed_title = trans(unicode(title.replace("_", "-").replace(".", "-")))[0]
                transformed_title = re.compile(r'[^\w+]').sub('-', transformed_title)
                transformed_title = re.compile(r'[-]+').sub('-', transformed_title)
                market['transformedTitle'] = transformed_title.lower()

            if ('Categories') in market:
                categories = market['Categories']
                comparison = markets_model.get_comparison(market['id'])
                
                for category in categories[:]:
                    yml_category_id = category['id']
                    if yml_category_id.isdigit():
                        yml_category_id = int(yml_category_id)
                        for comparison_item in comparison:
                            if yml_category_id == comparison_item['shop_cat_id']:
                                categories.remove(category)
            markets_model.save(market)

        CampaignsModel.adload.campaign_add('rynok', campaign_id)


    @staticmethod
    def get_campaign_status(campaign_id):
        campaign = CampaignsModel.get_by_id(campaign_id)
        if 'task_id' in campaign:
            result = AsyncResult(campaign['task_id'])

            if result.status == "SUCCESS":
                del campaign['task_id']
                CampaignsModel.campaign_collection.save(campaign)
                return result.get()
            elif result.status == "STARTED":
                return {"status": "in_rocess"}
            elif result.failed():
                del campaign['task_id']
                CampaignsModel.campaign_collection.save(campaign)
                result.get()
                return {"status": "failed", "msg": result.traceback}
            elif result.status == "RETRY":
                return {"status": "in_process"}
