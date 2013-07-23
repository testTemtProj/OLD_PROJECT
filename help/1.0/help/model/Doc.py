import MySQLdb
class Doc(object):
    def __init__(self):
        self.id = None
        self.projectId = None
        self.langId = None
        self.content = ''
        self.title = ''
        self.description = ''
        self.metakey = ''
        self.createDate = None
    def returnDict(self):
        result = {
                'id':int(self.id),
                'projectId':int(self.projectId),
                'langId':int(self.langId),
                'content':self.content.replace('"',"'"),
                'title':self.title.replace('"',"'"),
                'description':self.description.replace('"',"'"),
                'metakey':self.metakey.replace('"',"'"),
                'createDate':self.createDate
        }
        return result
            
