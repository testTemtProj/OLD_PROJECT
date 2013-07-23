# coding: utf-8

"""
	Скрипт аналогичный парсеру рынка но работает связано с двумя базами
	(использовать когда Adload RPC недоступна)
"""

import pymongo as p
from trans import trans
from manager.lib.set_category_count import *

import time
import xmlrpclib
#~ from manager.lib.tasks import *
#from tasks import *
class Parser():
    def __init__(self, market_id):
        self.rynok_db = p.Connection(['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']).rynok
        self.parser_db = p.Connection(['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']).parser
        self.market_id = market_id
        
        #~ ADLOAD_XMLRPC_HOST = "http://adload-rpc.yt/rpc"
        #~ adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)
        print "Parse Rynok!!"
        #print adload.get_offers('790dc147-3bab-4b8c-b26a-424e358d8678')
        
        t1 = time.time()
        print 'get offers'
        #self.market_offers = adload.get_offers_market_by_id(market_id)
        self.market_offers = []
        for x in self.parser_db.Offers.find({'shopId': market_id}):
            self.market_offers.append(x)
        t2 = time.time()
        print 'offers granted in time: %s'%(t2-t1)
        
        self.set_comporision()
        set_isLeaf(0)
        count_products(0)
    
    def set_comporision(self):
        t1 = time.time()
        print "start convert offers in products"
        comporision = self.rynok_db.Market.find_one({'id': int(self.market_id)})['comparision']
        for x in comporision:
            self.set_yottos_category(str(x['shop_cat_id']), x['y_cat_id'])
        t2 = time.time()
        print "Products added in time: %s"%(t2-t1)

    def set_market_count(self):
        try:
            count = self.rynok_db.Market.find_one({'id':self.market_id})['count'] + 1
            self.rynok_db.Market.update({'id':self.market_id},{'$set':{'count':count}})
        except:
            self.rynok_db.Market.update({'id':self.market_id},{'$set':{'count':0}})
            
    def set_category_count(self,cat_id):
        try:
            count = self.rynok_db.Category.find_one({'ID':cat_id})['count'] + 1
            self.rynok_db.Category.update({'ID':cat_id},{'$set':{'count':count}})
        except:
            self.rynok_db.Category.update({'ID':cat_id},{'$set':{'count':0}})
        return
    
    def delete_product(self, id):
        product = self.rynok_db.Products.find_one({'id': id})
        self.rynok_db.Products.remove({'id': id})
        count = self.rynok_db.Category.find_one({'ID':product['categoryId']})['count'] - 1
        if count > 0:
            self.rynok_db.Category.update({'ID':cat_id},{'$set':{'count':count}})
        count = self.rynok_db.Market.find_one({'id':self.market_id})['count'] - 1
        if count > 0:
            self.rynok_db.Market.update({'id':self.market_id},{'$set':{'count':count}})
        try:
            count = self.rynok_db.Vendors.find_one({'name':product['vendor']})['count'] - 1
            if count > 0:
                self.rynok_db.Vendors.update({'name':product['vendor']},{'$set':{'count':count}})
        except:
            pass
    
    def get_all_vendors(self):
        vendors = []
        for x in self.rynok_db.Vendors.find():
            vendors.append(x['name'])
            
        return vendors
    
    def set_vender(self, vendor_name):
        self.vendors = self.get_all_vendors()
        if vendor_name in self.vendors:
            vendor = self.rynok_db.Vendors.find_one({'name':vendor_name})
            
            try:
                count = self.rynok_db.Vendors.find_one({'name':vendor_name})['count'] + 1
            except:
                count = 1
                
            self.rynok_db.Vendors.update({'name':vendor_name},{'$set':{'count':count}})
            
            return vendor['id']
            
    
    def set_yottos_category(self, shop_cat_id, y_cat_id):
        #~ if len(self.market_offers)==0:
            #~ if self.market_offers_task.state!='SUCCESS':
                #~ self.market_offers_task.wait()            
            #~ self.market_offers = self.market_offers_task.result        
                #self.market_offers = adload.get_offers_market_by_id(market_id)['offers']
        for x in self.market_offers:
            if str(x['categoryId']) == shop_cat_id:
                try:
                    x['vendor'] = self.set_vender(x['vendor'])
                except:
                    x['vendor'] = 100000
                    
                if x['vendor'] == None:
                    x['vendor'] = 100000
                    
                title = x['title']
                title = title.replace(',', '')
                title = title.replace('.', '')
                title = title.replace(' ', '_')
                x['transTitle'] = trans(unicode(title))[0]
                x['categoryId'] = y_cat_id
                x['price'] = float(x['price'])
                try:
                    self.rynok_db.Products.find_one({'id':x['id']})['id']
                except:
                    self.set_market_count()
                    self.set_category_count(int(y_cat_id))
                    self.rynok_db.Products.update({'id':x['id']},x, upsert=True)
                
def delete_all():
    db = p.Connection(['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']).rynok
    #db.Products.remove()
    
    for x in db.Market.find():
        x['count'] = 0
        db.Market.save(x)
    
    for x in db.Category.find():
        x['count'] = 0
        db.Category.save(x)
        
    for x in db.Vendors.find():
        x['count'] = 0
        db.Vendors.save(x)
        
if __name__ == '__main__':
    print "Start"
    #delete_all()
    #Parser(104)
    print "End"
