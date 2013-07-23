# This file uses following encoding: utf-8
'''
Модель магазина
'''
from manager.model.baseModel import Base
from pymongo import DESCENDING as desc
from pymongo import ASCENDING as asc


class MarketsModel():
    
    market_collection = Base.market_collection


    @staticmethod
    def get_count():
        return MarketsModel.market_collection.find().count()
    
    
    @staticmethod
    def set_category(shop_id, categories):
        MarketsModel.market_collection.update({"id":shop_id}, {"$set":{'Categories':categories}}, upsert=True)
    

    @staticmethod
    def get_all(skip, limit):
        markets = []
        for x in MarketsModel.market_collection.find().sort('id', 1).skip(int(skip)).limit(int(limit)):
            markets.append(x)
        return markets
    

    @staticmethod
    def get_by_id(shop_id):
        market = MarketsModel.market_collection.find_one({"id":int(shop_id)})
        return market
    

    @staticmethod
    def save(market):
        MarketsModel.market_collection.update({'id':market['id']}, {'$set':market}, upsert = True, save=True)
    

    @staticmethod
    def get_comparison(market_id):
        market = MarketsModel.market_collection.find_one({'id': market_id})
        if market is None:
            return []

        if 'comparision' in market:
            return market['comparision']
        
        return []
    

    @staticmethod
    def set_comporison(shop_id, data):
        MarketsModel.market_collection.update({'id':int(shop_id)}, {"$set":{'comparision':data}})
        

    @staticmethod
    def set_time_settings(shop_id, data):
        MarketsModel.market_collection.update({'id':int(shop_id)}, {"$set":{'time_setting':data}})
