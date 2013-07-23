# This file using following encoding: utf-8
"""The application's Globals object"""

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from pymongo import Connection
import xmlrpclib
from pylons import config


class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self, config):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        self.config = config
        self.cache = CacheManager(**parse_cache_config_options(config))
        self.db = self.create_mongo_connection()

    def create_mongo_connection(self):
        ''' Подключается к монге, возвращает объект подключения '''
        connection = Connection(host=self.config.get('mongo_host', 'localhost'))
        db = connection[self.config.get('mongo_database', 'getmyad_db')]
        return db

    @property
    def adload_rpc(self):
        ''' Возвращает объект ServerProxy для AdLoad '''
        return xmlrpclib.ServerProxy(config['adload_xmlrpc_server'], use_datetime=True)

    @property
    def getmyad_rpc(self):
        ''' Возвращает объект ServerProxy для GetMyAd '''
        return xmlrpclib.ServerProxy(config['getmyad_xmlrpc_server'], use_datetime=True)
