# coding: utf-8

import sys
import os
import ConfigParser
import pymongo
import xmlrpclib
import base64  
import pickle  
import zlib
from datetime import datetime
#import re
#from trans import trans
from pprint import pprint


sys.path.append('.')
config_file = '%s/../../%s' % (os.path.dirname(__file__), "development.ini")
config = ConfigParser.ConfigParser()
config.read(config_file)

#TODO добавить обработки исключений

class CampaignOffersParser(object):

    database = pymongo.Connection(config.get('app:main', 'mongo_host'))[config.get('app:main', 'mongo_database')]
    campaign_collection = database.Advertise
    market_collection = database.Market
    vendor_collection = database.Vendors
    product_collection = database.Products
    category_collection = database.Category


    def __init__(self, campaign_id):
        self.campaign = self.campaign_collection.find_one({'idAdvertise':campaign_id})
        if not self.campaign:
            raise ValueError("campaign with id " + str(campaign_id) + " not found")
        

    def add_products(self):
        #TODO продумать, что если уже парсится другим объектом парсера, или закрашилась со статусом in_process
        current_campaign_status = self.campaign['state']['status']
        print "starting campaign with id " + str(self.campaign['idAdvertise'])
        if ('in_process' or 'started') == current_campaign_status :
            return

        self._set_status_message(status='in_process', message='Parser now handles the campaign', started='', finished='')

        #TODO продумать, какие могут быть исключения в адлоаде
        try:
            campaign_offers = self._get_offers_from_AdLoad()
        except:
            return self._set_status_message(status='stopped', message='Campaign stopped', started='', finished=datetime.now())

        # comparison_by_markets - {'MARKET_ID': {"CATEGORY_ID_IN_YML":'CATEGOY_ID_IN_RYNOK'}}
        comparison_by_markets = {}
        # comparison_by_vendor_names - {'VENDOR_NAME_IN_YML':'VENDOR_ID_IN_RYNOK'}
        comparison_by_vendor_names = {}
        offers_in_markets = {}
        offers_in_vendors = {}
        offers_in_category = {}

        not_valid_offers_count = 0
        valid_offers_count = 0
        not_compared_categories_count = 0
        compared_categories_count = 0
        total_offers_count = len(campaign_offers)
        
        for offer in campaign_offers[:]:
            if not self._validate_offer(offer):
                campaign_offers.remove(offer)
                not_valid_offers_count += 1
                continue
            
            market_id = offer['shopId']
            category_id = offer['categoryId']
            vendor_id = offer['vendor'] if 'vendor' in offer else ''

            if market_id not in comparison_by_markets:
                categories = self._get_compared_categories_by_market_id(market_id)
                comparison = categories['result']
                comparison_by_markets[market_id] = comparison
                compared_categories_count += len(comparison)
                not_compared_categories_count += categories['total']

            if category_id in comparison_by_markets[market_id]:
                category_id = comparison_by_markets[market_id][category_id]
            else:
                campaign_offers.remove(offer)
                continue

            if vendor_id not in comparison_by_vendor_names:
                comparison_by_vendor_names[vendor_id] = self._get_vendor_id_by_raw_vendor(vendor_id) 

            vendor_id = comparison_by_vendor_names[vendor_id]

            if market_id not in offers_in_markets:
                offers_in_markets[market_id] = 0

            if vendor_id not in offers_in_vendors:
                offers_in_vendors[vendor_id] = 0

            if category_id not in offers_in_category:
                offers_in_category[category_id] = 0

            offers_in_markets[market_id] += 1
            offers_in_vendors[vendor_id] += 1
            offers_in_category[category_id] += 1

            offer['categoryId'] = category_id
            offer['vendor'] = vendor_id 
            offer['campaign_id'] = self.campaign['idAdvertise']
            offer['popularity'] = 0

        valid_offers_count = len(campaign_offers) 

        if valid_offers_count:
            self.product_collection.insert(campaign_offers)

        for market_id in offers_in_markets.keys():
            self._increase_count_products_in_market(market_id, offers_in_markets[market_id])

        for vendor_id in offers_in_vendors.keys():
            self._increase_count_products_in_vendor(vendor_id, offers_in_vendors[vendor_id])

        for category_id in offers_in_category.keys():
            self._increase_count_products_in_category(category_id, offers_in_category[category_id])

        print "campaign with id " + str(self.campaign['idAdvertise']) + "successfuly started"
        return self._set_status_message(status='started', message='Campaign started', started=datetime.now(), finished='', statistics={'not_valid_offers':not_valid_offers_count, 'valid_offers':valid_offers_count, 'total_offers':total_offers_count, 'compared_categories':compared_categories_count, 'not_compared_categories':not_compared_categories_count})


    def remove_products(self):
        print "stopping campaign with id " + str(self.campaign['idAdvertise'])
        current_campaign_status = self.campaign['state']['status']
        if ('in_process' or 'started') == current_campaign_status :
            return

        started = datetime.now()
        self._set_status_message(status='in_process', message='Parser now handles the campaign', finished='')

        campaign_market_ids = map(lambda market: market['id'], self._get_markets_from_AdLoad())
        campaign_products = self.product_collection.find({'shopId':{'$in':campaign_market_ids}})

        products_in_markets = {}
        products_in_vendors = {}
        products_in_category = {}
        for product in campaign_products:
            market_id = product['shopId']
            vendor_id = product['vendor']
            category_id = product['categoryId']

            if market_id not in products_in_markets:
                products_in_markets[market_id] = 0

            if vendor_id not in products_in_vendors:
                products_in_vendors[vendor_id] = 0

            if category_id not in products_in_category:
                products_in_category[category_id] = 0

            products_in_markets[market_id] -= 1
            products_in_vendors[vendor_id] -= 1
            products_in_category[category_id] -= 1

            #TODO сделать одним запросом
            self.product_collection.remove(product)

        for market_id in products_in_markets.keys():
            self._increase_count_products_in_market(market_id, products_in_markets[market_id])

        for vendor_id in products_in_vendors.keys():
            self._increase_count_products_in_vendor(vendor_id, products_in_vendors[vendor_id])

        for category_id in products_in_category.keys():
            self._increase_count_products_in_category(category_id, products_in_category[category_id])
        
        print "campaign with id " + str(self.campaign['idAdvertise']) + "successfuly stopped"
        return self._set_status_message(status='stopped', message='Campaign stopped', finished=datetime.now())


    def update_products(self):
        current_campaign_status = self.campaign['state']['status']
        if ('in_process' or 'stopped') == current_campaign_status :
            return
        self.remove_products()
        self.add_products()

    
    def _validate_offer(self, offer):
        validate_fields = set(['shopId', 'categoryId'])

        if validate_fields.issubset(offer.keys()):
            return True

        return False


    def _get_offers_from_AdLoad(self):
        adload = xmlrpclib.ServerProxy(config.get('app:main','adload_xmlrpc_server'), allow_none=False)
        adload.__allow_none = True
        page = 0
        offers = []
        end = True
        while end:
            r = adload.get_offers_page(self.campaign['idAdvertise'], page)
            
            offers_chunk = pickle.loads(zlib.decompress(base64.urlsafe_b64decode(r)))
            if len(offers_chunk)==0:
                end = False
            else:
                offers.extend(offers_chunk)
            page += 1
        del(adload) 
        return offers


    def _get_markets_from_AdLoad(self):
        #TODO сделать проверки
        adload = xmlrpclib.ServerProxy(config.get('app:main','adload_xmlrpc_server'), allow_none=False)
        adload.__allow_none = True  
        return adload.get_shops_by_advertise(self.campaign['idAdvertise'])


    def _get_compared_categories_by_market_id(self, market_id):
        market = self.market_collection.find_one({'id' : market_id})
        if not market:
            return {}

        compared_categories = {}

        if 'comparision' in market:
            for comparison in market['comparision']:
                compared_categories[comparison['shop_cat_id']] = comparison['y_cat_id']

        categories_count = 0

        if 'Categories' in market:
            categories_count = len(market['Categories'])
       
        result = {'result' : compared_categories, 'total' : categories_count}

        return result


    def _get_vendor_id_by_raw_vendor(self, raw_vendor):
        #TODO сделать нормальное сопоставление производителя
        vendor = self.vendor_collection.find_one({'name': raw_vendor})
        if not vendor:
            none_vendor = self.vendor_collection.find_one({'name':'None vendor'})
            if not none_vendor:
                raise ValueError("Empty vendor not found. Please create it.")
            return none_vendor['id']

        return vendor['id']


    def _increase_count_products_in_category(self, category_id, increase):
        category = self.category_collection.find_one({'ID':category_id})
        if category is None:
            return
            #raise ValueError("category with id " + str(category_id)+ " not found")

        if category['ID'] is 0:
            return

        count = category['count'] if 'count' in category else 0
        count += increase
        category['count'] = count

        self.category_collection.save(category)

        parent_id = category['ParentID']
        self._increase_count_products_in_category(parent_id, increase)


    def _increase_count_products_in_market(self, market_id, increase):
        market = self.market_collection.find_one({'id':market_id})
        if market is None:
            return
            #raise ValueError("market with id " + str(market_id) + " not found")

        count = market['count'] if 'count' in market else 0
        count += increase
        market['count'] = count
        
        self.market_collection.save(market)


    def _increase_count_products_in_vendor(self, vendor_id, increase):
        vendor = self.vendor_collection.find_one({'id':vendor_id})
        if vendor is None:
            return
            #raise ValueError("vendor with id " + str(vendor_id) + " not found")

        count = vendor['count'] if 'count' in vendor else 0
        count += increase
        vendor['count'] = count

        self.vendor_collection.save(vendor)


    def _set_status_message(self, **kwargs):
        for key in kwargs:
            self.campaign['state'][key] = kwargs[key]
        self.campaign['last_update'] = datetime.now()
        self.campaign_collection.save(self.campaign)
