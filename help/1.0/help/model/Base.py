from pylons import app_globals
import PySQLPool
class Base(object):
    ''' DB model '''
    def __init__(self):
        self.db = app_globals.db
    def query(self):
        query = PySQLPool.getNewQuery(connection=self.db,commitOnEnd=True)
        return query

