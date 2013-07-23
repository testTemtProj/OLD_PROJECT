# coding: utf-8
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators.cache import *

from rynok.model.productsModel import ProductsModel
from rynok.model.treeModel import TreeModel
from webhelpers.html.builder import HTML
from rynok.lib.base import BaseController, render
from rynok.model.baseModel import Base
from rynok.model.categoriesModel import CategoriesModel
import re
import json
import pymongo.json_util
ITEM_COUNT = 10#кол-во товаров на странице
from pymongo import DESCENDING as desc
from pymongo import ASCENDING as asc

log = logging.getLogger(__name__)
productCount = 10
page = 1
class TestcacheController(BaseController):

    tree = None
    treeModel = None

    def test1(self):
        self.treeModel = TreeModel()
        self.tree = self.treeModel.getTree()
        c.Tree = HTML.literal(self.treeModel.renderTree(self.tree))
        return render('/test1.mako.html')

    def test(self):
        product = ProductsModel()
        c.Lot = product.getByCategoryId(1015)
        return render('/test.mako.html')
    def test2(self):
        db =  pymongo.Connection(['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']).rynok.Products
        product = []
        for x in db.find({"CategorID":1015}).skip((page - 1) * productCount).limit(productCount).sort("Weight", direction=asc):
            product.append(x)
        c.Lot = product
        return render('/test.mako.html')
#########################################
#ITEM_COUNT = 10#кол-во товаров на странице
#
#class ProductsModel:    
#    """Товарная единица"""
#    def __init__(self, count=ITEM_COUNT):        
#        base = Base()
#        self.Products = base.getProductCollections()
#        self.productCount = count 
#                                            
#    def save(self):
#        """Сохраняет товар в базу"""    
#        raise Exception("Savind not implemented")
#                
#    def getById(self, id):
#        """Загружает товар"""            
#        r = self.Products.find_one({'LotID':id})
#        if r is None:
#            raise Exception("Product is none")
#        return r
#        #return self.Products.find_one({'LotID':id})
#    
#    def _getProduct(self, field, value, page=1, sortField="Weight", direction=asc):
#        """Возвращает товары с учетом пейджинга, по умолчанию сортирует по 'весу' """
#        return [(x) for x in self.Products.find({field:value}).skip((page - 1) * self.productCount).limit(self.productCount).sort(sortField, direction=asc)]
#    
#    def getByTitle(self, title):
#        """Загружает товары по названию"""
#        print title
#        reTitle = re.compile(title, re.IGNORECASE)
#        #return [(x) for x in self.Products.find({field:value}).skip((page - 1) * self.productCount).limit(self.productCount).sort(sortField, direction=asc)]
#        return self._getProduct(field="Title", value=reTitle) 
#    
#    def getByCategoryId(self, id, page=1, field = "Weight", direction = asc):
#        """Возвращает товары по ИД категории, с учетом пейджинга, по умолчанию сортирует по 'весу' """        
#        return self._getProduct(field="CategorID", value=id)      
#                    
#    def _getCategories(self):
#        """ф-я получения списка категорий"""
#        db = Base().getCategoriesCollections()  
#        Categories = {}
#        for c in self.db.find:
#            self.Categories[c['ID']] = c['Title']
#        return Categories
#          
#    def getByCategoryName(self, name, page = 1, field = "Weight", direction = asc):
#        """Товары по названию категории """
#        category = CategoriesModel()
#        id  = category.getCategoryIdByName(name)     
#        return self.getByCategoryId(id, page, field, direction)
#      
#    def getByMarketID(self, id):    
#        """Товары по ид магазина """
#        return self._getProduct(field="ShopID", id=id)
#    
#    def JSON(self, obj, page = 1, field = "Weight", direction = asc):
#        """Возвращает JSON-представление объекта obj"""
#        return json.dumps(obj, default=pymongo.json_util.default, ensure_ascii=False)                  
#        
