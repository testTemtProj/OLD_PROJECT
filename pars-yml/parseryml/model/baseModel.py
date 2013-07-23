# coding: utf-8
from pymongo import Connection
#from pylons import app_globals
#from pylons import config
import os
import ConfigParser
PYLONS_CONFIG = "development.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config = ConfigParser.ConfigParser()
config.read(config_file)

class Base():
    """
    Модель подключения к базе
    """
    CONNECT_TO_MONGO = [config.get('app:main', 'mongo_host')]
    MONGO_DB = config.get('app:main', 'mongo_database')
    db = Connection(CONNECT_TO_MONGO)[MONGO_DB]
    connection = db 
#    def __init__(self): #['10.0.0.8:27018', '10.0.0.8:27017', '10.0.0.8:27019']
#        
#        self.connection = app_globals.db 
#        #pymongo.Connection(connections)[database]
#        #TODO: Не забыть о статистике
#        #self.statistics_connection = app_globals.db 
#        #pymongo.Connection(connections)
    @staticmethod
    def get_users_collection():
        return Base.connection.Users
    @staticmethod
    def get_product_collection():
        return Base.connection.Products
    @staticmethod
    def get_reference_collection():
        return Base.connection.Models
    @staticmethod
    def get_categories_collection():
        return Base.connection.Category
    @staticmethod
    def get_presentation_collection():
        return Base.connection.Presentation

#    def get_statistics_collection():
#        return Base.statistics_connection.statistics
    @staticmethod
    def get_market_collection():
        return Base.connection.Market
    @staticmethod
    def get_params_collection():
        return Base.connection.Params
    @staticmethod
    def get_Market_collection():
        return Base.connection.Market
    @staticmethod
    def get_offer_collection():
        return Base.connection.Offers
