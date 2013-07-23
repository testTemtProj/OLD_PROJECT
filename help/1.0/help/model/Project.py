from help.model.Base import Base
from pylons.i18n import get_lang
class Project(object):
    ''' DB model '''
    def __init__(self, controller=None, name=None, lang=None):
        self.controller = controller
        self.id = None
        self.name = name
        self.lang = lang
        self.langId = None
    def load(self):
        query = Base().query()
        if ((self.controller != None) and (self.name == None)):
            q = 'select * from project where controller = "%s"'%(self.controller)
        elif ((self.controller == None) and (self.name != None)):
            q = 'select * from project where name = "%s"'%(self.name)
        else:
            q = 'select * from project where controller = "%s"'%('main')
        query.query(q)
        row = query.record[0]
        self.id = int(row['id'])
        self.controller = str(row['controller'])
        self.name = str(row['name'])
        if (self.lang ==None):
            q = 'select id from lang where lang = "%s"'%(get_lang()[0])
        else:
            q = 'select id from lang where lang = "%s"'%(self.lang)
        query.query(q)
        row = query.record[0]
        self.langId = int(row['id'])
