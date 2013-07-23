# coding: utf-8
from manager.model.mongo_rebalance import ApplicationDatabaseInterface
import os
import ConfigParser
CONFIG = ConfigParser.ConfigParser()
CONFIG.read("%s/../../%s" % (os.path.dirname(__file__), "deploy.ini"))

class Base():
    
    database = CONFIG.get('app:main', 'mongo_database')
    connections = CONFIG.get('app:main', 'mongo_host').split(", ")
    connection = ApplicationDatabaseInterface(hosts=connections).connection()[database]

    campaign_collection = connection.Advertise
    categories_collection = connection.Category
    countries_collection = connection.geo.countries
    market_collection = connection.Market
    product_collection = connection.Products
    region_collection = connection.geo.regions
    settings_collection = connection.settings
    users_collection = connection.Users
    static_pages_collection = connection.StaticPages
