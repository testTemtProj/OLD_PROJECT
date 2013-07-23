import pymongo
import catalog.lib.sphinxapi as sphinxapi
import ConfigParser
import os
CONFIG = ConfigParser.ConfigParser()
CONFIG.read("%s/../../%s" % (os.path.dirname(__file__), "deploy.ini"))

class Base():
    """
    connection to DB model
    """
    database=CONFIG.get ('app:main','mongo_database')
    connections = CONFIG.get('app:main', 'mongo_host')
    #connection = ApplicationDatabaseInterface(hosts=connections).connection()[database]
    connection = pymongo.Connection(connections)[database]
    #connection = pymongo.Connection().catalog
    category_collection = connection.category
    site_collection = connection.site
    users = connection.user

    sph_port = CONFIG.get('app:main', 'sphinx_port')
    sph_host = CONFIG.get('app:main', 'sphinx_host')
    sphinx_client = sphinxapi.SphinxClient()
    sphinx_client.SetServer(sph_host,int(sph_port))

