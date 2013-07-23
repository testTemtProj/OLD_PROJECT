# coding: utf-8
#from pymongo import ASCENDING as asc
from pymongo import DESCENDING as desc

from rynok.model.baseModel import Base
import json
import datetime
import pymongo
# from manager.validate.schema import *

class ReferenceItem(object):
    """
    Шаблон обертки эталона
    """

    # TODO сделать валидацию
    """
    schema = {
            'ShopTransName' : String,
            'VendorCode': String,
            'ShopName' : String,
            'Descr' : String,
            'Title' : String,
            'Param' : List,
            'Translited' : String,
            'StartDate' : Nevermind,
            'Vendor' : String,
            'Price' : String,
            'ShopID' Integer
        }
    """
    def __init__(self, obj=None):
        if obj:
            self.populate(obj)

    def populate(self, obj):
        if not isinstance(obj, dict):
            raise TypeError("Instance of object must be a dictionary")
        for key, value in obj.iteritems():
            vars(self)[key] = value
        return self

    def to_dict(self):
        return vars(self)

    def save(self):
        reference_collection = Base.products_collection

        if vars(self).has_key("id"):
            if vars(self).has_key('_id'):
                reference_collection.save(self.to_dict())
            else:
                self._id = reference_collection.find_one({"id": self.id})["_id"]

            reference_collection.save(self.to_dict())
        else:
            last = reference_collection.find().sort('id', desc)[0]
            id = int(last["id"]) + 1
            self.id = id
            self._id = reference_collection.save(self.to_dict())

        return self

    def jsonify(self, raw=False):
        obj = self.to_dict()
        #del(obj['_id'])
        for key in obj:
            if isinstance(obj[key], datetime.datetime):
                obj[key] = obj[key].strftime("%Y-%m-%d %H:%M:%S")

            if isinstance(obj[key], list):
                for item in obj[key]:
                    if isinstance(item, dict):
                        for _key in item:
                            if isinstance(item[_key], datetime.datetime):
                                item[_key] = item[_key].strftime("%Y-%m-%d %H:%M:%S")
        if raw:
            return obj

        return json.dumps(obj, default=pymongo.json_util.default, ensure_ascii=False)

    def __len__(self):
        return len(vars(self))

    def __getitem__(self, index):
        if hasattr(self, index):
            return getattr(self, index)
        else:
            return None

    def __setitem__(self, key, item):
        setattr(self, key, item)

    def __getattribute__(self, index):
        try:
            return object.__getattribute__(self, index)
        except AttributeError:
            return None
