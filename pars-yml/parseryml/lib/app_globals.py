# This file using following encoding: utf-8
"""The application's Globals object"""

#from beaker.cache import CacheManager
#from beaker.util import parse_cache_config_options
from pymongo import Connection

from pylons import config

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        #self.cache = CacheManager(**parse_cache_config_options(config))
        self.connection = Connection(host=config.get('mongo_host', '127.0.0.1:27017'))
        self.db = self.connection[config.get('mongo_database', 'parser')]
        #TODO: Не забыть о статистике
        #self.stat_db = self.connection[config.get('statistic_mongo_database', 'stat_db')]
