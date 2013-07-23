from rynok.model.baseModel import Base

class VendorsModel(object):
    
    vendors_collection = Base.vendors_collection
        
    @staticmethod
    def get_all(non_empty=True):
        query = {}
        if non_empty:
                query = {'count': {'$gt' : 0}, 'id' : {'$ne' : 100000}}
        return VendorsModel.vendors_collection.find(query, slave_okay=True).sort('name', 1)

    @staticmethod
    def get_by_id(vendor_id):
        try:
            return VendorsModel.vendors_collection.find_one({'id':int(vendor_id)}, slave_okay=True) 
        except ValueError:
            print 'vendorsModel.py:17 vendor_id must be integer!!!'
            
    @staticmethod
    def get_by_ids(ids):
        if not isinstance(ids, list):
            raise Exception('ids must be list')
        int_ids = []
        for vendor_id in ids:
            if isinstance(vendor_id, str) and vendor_id.isdigit():
                vendor_id = int(vendor_id)
            int_ids.append(vendor_id)
            
        return VendorsModel.vendors_collection.find({'id':{'$in':int_ids}}, slave_okay=True)

    @staticmethod
    def get_by_transformedTitle(transformedTitle):
        return VendorsModel.vendors_collection.find_one({'transformedTitle': transformedTitle}, slave_okay=True)
