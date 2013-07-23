# This file using following encoding: utf-8
"""The application's Globals object"""

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from pylons import config
from pymongo import Connection

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self, config):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        self.cache = CacheManager(**parse_cache_config_options(config))
        self.connection = Connection(host=config.get('mongo_host', 'localhost'))
        self.db = self.connection[config.get('mongo_database', 'rynok_db')]
        #TODO: Не забыть о статистике
        #self.stat_db = self.connection[config.get('statistic_mongo_database', 'stat_db')]
