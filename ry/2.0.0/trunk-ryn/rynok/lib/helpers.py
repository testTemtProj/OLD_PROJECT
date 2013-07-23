# coding: utf-8
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
import zlib
import pickle
import json
import pymongo.json_util

from base64 import urlsafe_b64encode
from base64 import urlsafe_b64decode
from webhelpers.html.tags import *
from webhelpers.html.builder import HTML
from webhelpers.html import escape, HTML, literal, url_escape
from routes import url_for
from trans import trans
#from minwebhelpers import *

from rynok.model.categoriesModel import CategoriesModel
from rynok.model.item.referenceItem import ReferenceItem
from rynok.model.vendorsModel import VendorsModel
from rynok.model.marketsModel import MarketsModel
from rynok.model.referenceModel import ReferenceModel
from rynok.model.navigation import NavigationAbstract

def JSON(obj):
    """Возвращает JSON-представление объекта obj"""
    return json.dumps(obj, default=pymongo.json_util.default, ensure_ascii=False)

def translate(s):
    """Возвращает транслетированую строку"""
    s = s.replace(" ","_")
    return trans(s)[0]


categories_model = CategoriesModel

# не подлежит кешированию
def get_categories(rootId, deep=1024):
    cats = []
    if not deep:
        return cats

    for category in categories_model.getChildrens(rootId):
        cats.append({"category": category, "childrens": get_categories(category['ID'], deep - 1)})

    return cats
    
def get_vendors():
    vendors_model = VendorsModel
    return vendors_model.get_all()

def get_vendors_by_market(market_id):
    reference_model = ReferenceModel
    vendors_model = VendorsModel
    tempo = reference_model.group(keys={'vendor':True}, condition={'shopId':market_id})
    
    vendors = []
    for item in tempo:    
        vendors.append(item['vendor'])

    return vendors_model.get_by_ids(vendors)

def get_markets_by_vendor(vendor_id):
    """
    Возвращает магазины товаров данного производителя
    Входные параметры:
        vendor_id = (int) - id производителя
    Возвращает:
        markets = [{} (dict)] (list)  - массив магазинов товаров данного производителя
    """
    reference_model = ReferenceModel
    markets_model = MarketsModel
    tempo = reference_model.group(keys={'shopId':True}, condition={'vendor':vendor_id})
    shops = []
    for item in tempo:
        shops.append(item['shopId'])

    return markets_model.get_by_ids(shops)

def get_vendors_by_category_and_market(category_id, market_id):
    vendors_model = VendorsModel
    reference_model = ReferenceModel

    tempo = reference_model.group(keys={'vendor':True}, condition={'categoryId': category_id, 'shopId': market_id})
    
    vendors = []
    for item in tempo:
        vendors.append(item['vendor'])

    return vendors_model.get_by_ids(vendors)

def get_markets_by_category_and_vendor(category_id, vendor_id):
    """
    Выбирает все магазины по категория для данного производителя
    Входные параметры:
        category_id = (int) - id текущей категории
        vendor_id = (int) - id текущего производителя
    Возвращает:
        result = [{} (dict)] (list) - массив магазинов для категории данного производителя
    """
    markets_model = MarketsModel
    reference_model = ReferenceModel

    tempo = reference_model.group(keys={'shopId':True}, condition={'categoryId': category_id, 'vendor': vendor_id})
    
    markets = []
    for item in tempo:
        markets.append(item['shopId'])

    return markets_model.get_by_ids(markets)


def get_markets_by_category(category_id):
    markets_model = MarketsModel
    reference_model = ReferenceModel
    tempo = reference_model.group(keys={'shopId':True}, condition={'categoryId':category_id})
    markets = []
    for item in tempo:
        markets.append(item['shopId'])

    return markets_model.get_by_ids(markets)


def get_vendors_by_category(category_id):
    vendors_model = VendorsModel
    reference_model = ReferenceModel

    tempo = reference_model.group(keys={'vendor': True}, condition={'categoryId':category_id})

    vendors = []
    for item in tempo:
        vendors.append(item['vendor'])

    return vendors_model.get_by_ids(vendors)


def get_markets():
    markets_model = MarketsModel
    return markets_model.get_all() 

cats = []
def get_breadcrumbs(category_id, f = True):
	if f:
		global cats
		cats = []
	CM = CategoriesModel
	parent_cat = CM.getParentCategory(category_id)
	cur_cat = CM.getCategoryById(category_id)
	cats.append(cur_cat['Name'])
	if cur_cat['ParentID'] != 0:
		get_breadcrumbs(cur_cat['ParentID'], False)
	return cats

def price_to_int(price):
	try:
		int(price[0:len(price)-1])
		return int(price)
	
	except:
		i = 1
		for x in range(0,len(price)):
			try:
				int(price[0:i])
				i += 1
			except:
				return int(price[0:i-1])

def get_market_favicon(market_title):
	MM = MarketsModel
	market = MM.get_market_by_title(market_title)
	return market['urlMarket']+'/favicon.ico'

def get_all_products(product_title):
	PM = ProductsModel()
	products = PM.getProduct(where = {'Title':product_title})
	return products
	
def get_currency(product_title):
	PM = ProductsModel()
	return PM.getProduct(where = {'Title':product_title}, by = 'Price', one = True, direction = 'desc')['Currency']

def get_average_price(product_title):
	PM = ProductsModel()
	average_price = 0
	products = PM.getProduct(where = {'Title':product_title})
	for x in products:
		average_price += price_to_int(x['Price'])
	average_price = average_price/len(products)
	return average_price
	
def get_max_price(product_title):
	PM = ProductsModel()
	price = PM.getProduct(where = {'Title':product_title}, by = 'Price', one = True)['Price']
	return price_to_int(price)

def get_min_price(product_title):
	PM = ProductsModel()
	price = PM.getProduct(where = {'Title':product_title}, by = 'Price', one = True, direction = 'desc')['Price']
	return price_to_int(price)

def get_count_products(product_title):
	PM = ProductsModel()
	return len(PM.getProduct(where = {'Title':product_title}))

def remove_dublicates(store):
    """
    Удаляет дубликаты из массива
    """
    return list(set(store))

def encode(params):
    """
    Кодирование параметров для передачи ссылкой
    Ф-я принимает список параметров 
    """
    return urlsafe_b64encode(zlib.compress(pickle.dumps(params)))

def decode(str):
    """
    Декодирование параметров из ссылкой
    Ф-я принимает список строку в base64 
    """
    bs = urlsafe_b64decode(str)    
    zs = zlib.decompress(bs)

    return pickle.loads(zs)
        
def round_rating(rating):
    """
    Округляет рейтинг до целого или половины
    """
    if (rating > 5) or (rating < 0):
        raise Exception('rating must be > 0 and < 5')

    fractional_part = rating-int(rating)
    if fractional_part < 0.25:
        fractional_part = 0
    elif (fractional_part >= 0.25 and fractional_part < 0.5) or (fractional_part < 0.75 and fractional_part >= 0.5):
        fractional_part = 0.5
    else:
        fractional_part = 1
    rating = int(rating) + fractional_part

    return rating    


def get_navigation_tree(navigation_model):
    if not issubclass(navigation_model.__base__, NavigationAbstract):
        raise Exception('navigation_model must be a subclass of NavigationAbstract')

    def get_tree(root_item_id=0, deep=1):
        if not deep:
            return None

        navigation_tree_item = {}
        navigation_tree_item['item'] = navigation_model.get_by_id(root_item_id)
        navigation_tree_item['children'] = []

        for navigation_item in navigation_model.get_by_parent_id(root_item_id):
            children = get_tree(navigation_item['id'], deep-1)
            if children is not None:
                navigation_tree_item['children'].append(children)

        return navigation_tree_item

    return get_tree
