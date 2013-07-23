# coding: utf-8
from rynok.model.baseModel import Base

class PopularProductsModel(object):
    popular_products_collection = Base.popular_products_collection
    
    @staticmethod
    def get_all(fields=None):
        return PopularProductsModel.popular_products_collection.find(fields=fields, slave_okay=True)
