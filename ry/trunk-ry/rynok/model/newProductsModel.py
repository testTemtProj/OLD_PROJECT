# coding: utf-8
from rynok.model.baseModel import Base

class NewProductsModel(object):
    new_products_collection = Base.new_products_collection
    
    @staticmethod
    def get_all(cursor=True):
        products = NewProductsModel.new_products_collection.find(slave_okay=True)
        if cursor:
            return products
        else:
            result = []
            for product in products:
                result.append(product)
            return result
