# this file using following encoding: utf-8
"""The application's Globals object"""

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from pylons import config
import PySQLPool

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
        self.config = config
        self.db = self.__create_connection()

    def __create_connection(self):
        '''Подключается к бд и возвращает объект пула подключения'''
        db = PySQLPool.getNewConnection(host = self.config.get('db_host', 'localhost'), username = self.config.get('db_user', 'root'),\
                password = self.config.get('db_password', '123qwe'), db = self.config.get('db_name', 'help'), commitOnEnd=True, use_unicode=True, charset='utf8')
        return db
