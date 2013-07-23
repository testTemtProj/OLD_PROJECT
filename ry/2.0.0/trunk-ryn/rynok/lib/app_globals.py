# coding: utf-8
"""The application's Globals object"""

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from pylons import config

from beaker.cache import cache_region

#from rynok.model.mongo_rebalance import *

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

        CONNECT_TO_MONGO = [config.get('mongo_host')]
        MONGO_DB = config.get('mongo_database')
        db = Connection(CONNECT_TO_MONGO)[MONGO_DB]
        self._db = db
        self.cache = CacheManager(**parse_cache_config_options(config))
        
        """
        Настройки главной страницы
        """
        main_page_settings = db.settings.find_one({'name': 'mainPage'})
        del main_page_settings['_id']

        self.main_page_settings = main_page_settings
        
        #TODO: вынести в конфиг
        self.cdnt = config.get('url_cdn', 'http://cdnt.yottos.com')
        self.domain = 'http://rynok.yt'
