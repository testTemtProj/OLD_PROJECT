# coding: utf-8
import pymongo as p
from rynok.model.baseModel import Base
from rynok.model.productsModel import ProductsModel
from rynok.model.categoriesModel import CategoriesModel

class test_base_model():
    def setUp(self):
        self.con = p.Connection()
        self.con.drop_database('test_rynok')
        self.db = self.con.test_rynok                         
    def tearDown(self):
        self.con.disconnect()
        pass
    def test_products_model(self):
        db = self.db
        item = {
    "VendorCode" : "",
    "ShopName" : "AromaCity",
    "Descr" : "Серьги Риск",
    "Title" : "Серьги Риск",
    "Param" : [ ],
    "StartDate" : "Mon Feb 28 2011 18:54:19 GMT+0200 (EEST)",
    "Vendor" : "",
    "Price" : "110 $",
    "ShopID" : 1,
    "PriceHistory" : [
        {
            "date" : "Mon Feb 28 2011 18:54:19 GMT+0200 (EEST)"
        },
        {
            "price" : "110 $"
        }
    ],
    "Date" : "Fri Nov 05 2010 06:51:28 GMT+0200 (EEST)",
    "URL" : "http://aromacity.com.ua/kupit_sergi_risk.html",
    "ImageURL" : "http://rynok.yottos.ru/img/154/9ba0b283-8cdd-4932-b592-0b52df94eef8.jpg",
    "ClickCost" : 0.43,
    "CurrencyArray" : [
        {
            "usd" : "8.93"
        },
        {
            "EUR" : "CBRF"
        }
    ],
    "URLconf" : 2,
    "LotID" : 1,
    "CategorID" : 1,
    "Weight" : 1,
    "Currency" : "UHR",
    "AdCampaignID" : 1
}
        db.Products.insert(item)
        product = ProductsModel(connections = "127.0.0.8:27017", database = "test_rynok")
        p = product.getById(1)
#        print  p['LotID']==item['LotID']
        assert p['LotID'] == item['LotID']
        assert product.getByTitle("Серьги Риск")['LotID'] == item['LotID']
        assert product.getByCategoryId(1)['LotID'] == item['LotID']

    def test_category_model(self):
        con = p.Connection()
        db = con.rynok
        post = {'ID': 1, 'ParentID': 0, 'Name': 'test_category', 'CountLot': 100, 'Title': 'test_category', 'Description': 'test_category', 'MetaKey': 'test_category'}
        db.Category.insert(post)
        categories = CategoriesModel()
        assert categories.getCategoryById(1) == db.Category.find_one({"ID": 1})
        assert categories.getCategoryByName('test_category') == db.Category.find_one({"Name": 'test_category'})
        assert categories.getCategoryIdByName('test_category') == db.Category.find_one({"Name": 'test_category'}).get("ID", False)
        children = []
        for currentCategory in db.Category.find({"ParentID": 1}):
            children.append(currentCategory)
        assert categories.getChildrens(1) == children
        category = db.Category.find_one({"ID":1})
        assert categories.getParentCategory(1) == db.Category.find_one({"ID":category['ParentID']})
        all = []
        for currentCategory in db.Category.find():
            all.append(currentCategory)
        assert categories.getAll() == all
        parent = []
        for category in db.Category.find({'ParentID': 0}).sort('Name', 1):
            parent.append(category)
        assert categories.getCategoriesByParentId(0) == parent
