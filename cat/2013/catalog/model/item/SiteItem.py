from catalog.model.modelBase import Base
import pymongo
import datetime
import re
from bson.objectid import ObjectId as objectid

class SiteItem(object):
    def __init__(self, obj=None):
        if obj:
            self.populate(obj)
    
    def populate(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.iteritems():
                vars(self)[key] = value
            return self
        else:
            raise TypeError("Must be dictionary")
        return self

    @property
    def to_dict(self):
        return vars(self)

    #@to_dict.setter
    def set_field(self, field, value):
        vars(self)[field] = value

    #@to_dict.deleter
    def del_field(self, field):
        del vars(self)[field]

    def save(self):
        collection  = Base.site_collection
        if 'id' in vars(self):
            if vars(self).has_key('_id'):
                pass
            else:
                self._id = objectid(collection.find_one({"id": self.id})['_id'])
        else:
            self.id = (1 + int(collection.find().sort('id', pymongo.DESCENDING)[0]['id'])) if collection.count() else 0
        self._format_data()
        #if self._validate():
        collection.save(self.to_dict)
        return self

    def delete(self):
        collection = Base.site_collection
        collection.remove({"id": int(self.id)})
            
    def update(self):
        collection  = Base.site_collection
        self._format_data()
        if collection.find_one({'id': self.id}):
            collection.update({"id":self.id},self.to_dict)
        else:
            del self.id
            self.save()
        
    def __iter__(self):
        return vars(self)

    def next(self):
        pass
      
    def __getattribute__(self,index):
        try:
            return object.__getattribute__(self, index)
        except AttributeError:
            return None
    
    def _validate(self):
        #fields need to be represented
        fields = ['id','category_id','name','reference','description','owners_mail']
        for field in fields:
            if not field in vars(self):
                return False 
        return True

    def _format_data(self):
        fields = ['id','category_id','reference','name_ru','description_ru','name_uk','description_uk','name_en','description_en','owners_mail','date_add', 'checked', 'avaible', 'rate', 'last_checked']
        keys = [key for key in self.to_dict]
        for field in keys:
            if field not in fields:
                self.del_field(field)

        if not isinstance(self.category_id, int):
            self.category_id = int(self.category_id)

        if not isinstance(self.date_add, datetime.datetime):
            self.date_add = datetime.datetime(*[int(i) for i in str(re.search(r'\d{4}-\d{1,2}-\d{1,2}', str(self.date_add)).group()).split('-')])

        if self.last_checked: 
            if not isinstance(self.last_checked, datetime.datetime):
                self.last_checked = datetime.datetime(*[int(i) for i in str(re.search(r'\d{4}-\d{1,2}-\d{1,2}', str(self.last_checked)).group()).split('-')])

            else:
                self.last_checked = self.date_add

        return self
