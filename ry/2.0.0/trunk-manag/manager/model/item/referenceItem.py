# coding: utf-8
from pymongo import ASCENDING as asc
from pymongo import DESCENDING as desc

from manager.model.baseModel import Base
import json
import datetime
import pymongo
# from manager.validate.schema import *

class ReferenceItem():
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
        base_model = Base()
        reference_collection = base_model.get_reference_collection()

        if vars(self).has_key("LotID"):
            self._id = reference_collection.find_one({"LotID": self.LotID})["_id"]
            print self.to_dict()
            reference_collection.save(self.to_dict())
        else:
            last = reference_collection.find().sort('LotID', desc)[0]
            id = int(last["LotID"]) + 1
            self.LotID = id
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
