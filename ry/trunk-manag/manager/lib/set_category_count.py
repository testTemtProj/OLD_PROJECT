# coding: utf-8

#from pylons import config
from pymongo import  Connection


import os
import ConfigParser
PYLONS_CONFIG = "development.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config = ConfigParser.ConfigParser()
config.read(config_file)
#LOG = logging.getLogger(__name__)
ADLOAD_XMLRPC_HOST = config.get('app:main', 'adload_xmlrpc_server')

cats = Connection([config.get('app:main', 'mongo_host')])[config.get('app:main', 'mongo_database')].Category
products = Connection([config.get('app:main', 'mongo_host')])[config.get('app:main', 'mongo_database')].Products

def count_categories():
    
    """
        Функция для прощета количества товаров корневых категориях
    """
    
    categories = cats.find({'isLeaf': True})
    for cat in categories:
        count = products.find({'categoryId': cat['ID']}).count()
        cat['count'] = count
        cats.save(cat)

def count_products(root):
    
    """
        Функция для прощета количества товаров в категориях каскадным путем 
        от листьев до главных категорий
        
        Передаеться:
            root - идинтификатор категории которую считать верхней
    """
    
    root_cat = cats.find_one({'ID': root})

    if root_cat.has_key('isLeaf') and root_cat['isLeaf']:
        try:
            return root_cat['count']
        except:
            return 0

    childrens = cats.find({'ParentID': root})

    count = 0

    for children in childrens:
        count += count_products(children['ID'])

    root_cat['count'] = count
    cats.save(root_cat)
    
    return count

def set_popular(root):
    
    """
        Функция для прощета популярности категорий коскадным путем  от 
        листьев до главных категорий
        
        Передаеться:
            root - идинтификатор категории которую считать верхней
    """
    
    root_cat = cats.find_one({'ID': root})

    if root_cat['isLeaf']:
        if root_cat.has_key('popularity'):
            return root_cat['popularity']
        else:
            return 0

    childrens = cats.find({'ParentID': root})

    count = 0

    for children in childrens:
        count += set_popular(children['ID'])

    root_cat['popularity'] = count
    cats.save(root_cat)
    
    return count

def set_isLeaf(root):
    
    """
        Функция для обозначения корневых категорий в дереве
        
        Передаеться:
            root - идинтификатор категории которую считать верхней
    """
    
    root_cat = cats.find_one({'ID': root})
    
    childrens = cats.find({'ParentID': root})

    if childrens.count():
        root_cat['isLeaf'] = False
    else:
        root_cat['isLeaf'] = True 

    cats.save(root_cat)

    for ch in childrens:
        set_isLeaf(ch['ID'])

count_categories()
