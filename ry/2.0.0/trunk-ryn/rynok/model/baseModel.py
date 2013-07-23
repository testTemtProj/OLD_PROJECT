# coding: utf-8

from rynok.model.mongo_rebalance import ApplicationDatabaseInterface
import os
import ConfigParser
CONFIG = ConfigParser.ConfigParser()
CONFIG.read("%s/../../%s" % (os.path.dirname(__file__), "deploy.ini"))

class Base():
    """
    Модель подключения к базе
    """
    database = CONFIG.get('app:main', 'mongo_database')
    connections = CONFIG.get('app:main', 'mongo_host').split(", ")
    connection = ApplicationDatabaseInterface(hosts=connections).connection()[database]

    products_collection = connection.Products
    category_collection = connection.Category
    vendors_collection = connection.Vendors
    market_collection = connection.Market
    new_products_collection = connection.NewProducts
    popular_products_collection = connection.PopularProducts
    static_pages_collection = connection.StaticPages
    settings_collection = connection.settings
