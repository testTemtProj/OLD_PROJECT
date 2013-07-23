# coding: utf-8
from rynok.model.baseModel import Base

class MarketsModel(object):
    market_collection = Base.market_collection
    
    @staticmethod
    def get_by_id(id):
        return MarketsModel.market_collection.find_one({'id':int(id)}, slave_okay=True)

    @staticmethod
    def get_by_transformedTitle(title):
        return MarketsModel.market_collection.find_one({'transformedTitle': str(title)}, slave_okay=True)
    
    @staticmethod
    def get_all(non_empty=True):
        """
        Возвращает список магазинов 
        """        
        query = {}
        if non_empty:
            query = {'count' : {'$gt' : 0}}
        return MarketsModel.market_collection.find(query, slave_okay=True).sort("title", 1)
            
    @staticmethod
    def get_by_ids(ids):
        """Возвращет """
        if not isinstance(ids, list):
            raise Exception('ids must be list')
        return MarketsModel.market_collection.find({'id':{'$in':ids}}, slave_okay=True)
