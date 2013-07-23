from help.model.Base import Base
from help.model.Doc import Doc
from pylons.i18n.translation import get_lang
import datetime

class News(object):
    def __init__(self, projectId, langId):
        self.projectId = projectId
        self.langId = langId

    def returnOne(self, date = None, id = None):
        id = id
        date = date
        doc = Doc()
        query = Base().query()
        if (id == None ):
            if isinstance(date, datetime.datetime):
                q = 'select * from news where project_id = %d and create_date = "%s" and lang_id = %d LIMIT 0 , 1'%(self.projectId, date.strftime("%Y-%m-%d %H:%M:%S"), self.langId)
            else:
                q = 'select * from news where project_id = %d and lang_id = %d  order by create_date desc LIMIT 0 , 1'%(self.projectId, self.langId)
        else:
            q = 'select * from news where project_id = %d and lang_id = %d and id= %d LIMIT 0 , 1'%(self.projectId, self.langId, int(id))
        query.query(q)
        count = 0
        for row in query.record:
            doc.id = row.get('id',None)
            doc.projectId = row.get('project_id',None)
            doc.langId = row.get('lang_id',None)
            doc.content = row.get('content','')
            doc.title = row.get('title','')
            doc.description = row.get('description','')
            doc.metakey = row.get('metakey','')
            doc.createDate = row.get('create_date',None)
        return doc

    def returnAll(self, skip=None, limit=None):
        query = Base().query()
        if ((skip == None) and (limit==None)):
            q = 'select * from news where project_id = %d and lang_id = %d order by create_date desc'%(self.projectId, self.langId)
        elif ((skip == None) and (limit!=None)):
            q = 'select * from news where project_id = %d and lang_id = %d order by create_date desc LIMIT %d,%d'%(self.projectId, self.langId, 0, limit)
        elif ((skip != None) and (limit!=None)):
            q = 'select * from news where project_id = %d and lang_id = %d order by create_date desc LIMIT %d,%d'%(self.projectId, self.langId, skip, limit)
        else:
            q = 'select * from news where project_id = %d and lang_id = %d order by create_date desc LIMIT %d,%d'%(self.projectId, self.langId, 0, 10)
        query.query(q)
        result = []
        for row in query.record:
            doc = Doc()
            doc.id = row.get('id',None)
            doc.projectId = row.get('project_id',None)
            doc.langId = row.get('lang_id',None)
            doc.content = row.get('content','')
            doc.title = row.get('title','')
            doc.description = row.get('description','')
            doc.metakey = row.get('metakey','')
            doc.createDate = row.get('create_date',None)
            result.append(doc)
        return result

    def save(self,doc):
        query = Base().query()
        doc.projectId = self.projectId
        doc.langId = self.langId
        if doc.id != None:
            q = '''update news set content = "%(content)s", title = "%(title)s", description = "%(description)s", metakey = "%(metakey)s" where id = %(id)s'''%(doc.returnDict())
        else:
            q = '''insert into news (content,title,description,metakey,project_id,lang_id) VALUES ("%(content)s","%(title)s","%(description)s","%(metakey)s","%(projectId)s","%(langId)s") '''%(doc.returnDict())
        query.query(q)
