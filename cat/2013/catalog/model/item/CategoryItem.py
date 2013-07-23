from catalog.model.modelBase import Base
import pymongo

class CategoryItem(object):
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

    @property
    def to_dict(self):
        return vars(self)

    @to_dict.setter
    def set_field(self, field, value):
        vars(self)[field] = value

    @to_dict.deleter
    def del_field(self, field):
        del vars(self)[field]


    def save(self):
        collection  = Base.category_collection
        # if self._validate():
        #     collection.save(self)
        #     return self
        # else:
        #     return "Error! Not all fields with values!"

        if 'id' in vars(self):
            if '_id' in vars(self):
                pass
            else:
                self._id = collection.find_one({"id": self.id})["_id"]                

        else:
            self.id = (1 + int(collection.find().sort('id', pymongo.DESCENDING)[0]['id'])) if collection.count() else 0
        if self._validate():
            collection.save(self.to_dict)
            return self
        else: 
            return False

    def delete(self):
        collection = Base.category_collection
        collection.remove({"id":int(self.id)})
        return self
        
    def get_children(self,deep=1):
        collection = Base.category_collection
        parent_id = int(vars(self)['id'])
        children = [self]
        if deep >=0:
            for cat in collection.find({'parent_id':parent_id}):
                children.append(CategoryItem(cat).get_children(deep-1)) 

        return children
    
    
    def __iter__(self):
        return vars(self).next()
    
    def next(self):
        yield vars(self)
    
    def __getattribute__(self,index):
        try:
            return object.__getattribute__(self, index)
        except AttributeError:
            return None
        
    def _validate(self):
        fields = ['id','slug','is_leaf','title','parent_id']
        for field in fields:
            if not field in vars(self):
                return False
        return True

