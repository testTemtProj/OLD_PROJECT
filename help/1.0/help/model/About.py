from help.model.Base import Base
from help.model.Doc import Doc
from pylons.i18n.translation import get_lang

class About(object):
    def __init__(self, projectId, langId):
        self.projectId = projectId
        self.langId = langId

    def returnOne(self):
        query = Base().query()
        doc = Doc()
        query.query('select * from about where project_id = %d and lang_id = %d LIMIT 0 , 1'%(self.projectId, self.langId))
        for row in query.record:
            doc.id = row.get('id',None)
            doc.projectId = row.get('project_id',None)
            doc.langId = row.get('lang_id',None)
            doc.content = row.get('content','')
            doc.title = row.get('title','')
            doc.description = row.get('description','')
            doc.metakey = row.get('metakey','')
        return doc

    def save(self,doc):
        query = Base().query()
        doc.projectId = self.projectId
        doc.langId = self.langId
        if doc.id != None:
            q = '''update about set content = "%(content)s", title = "%(title)s", description = "%(description)s", metakey = "%(metakey)s" where id = %(id)d'''%(doc.returnDict())
        else:
            q = '''insert into about (content,title,description,metakey,project_id,lang_id) VALUES ("%(content)s","%(title)s","%(description)s","%(metakey)s",%(projectId)d,%(langId)d) '''%(doc.returnDict())
        query.query(q)
