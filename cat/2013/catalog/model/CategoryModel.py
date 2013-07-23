from catalog.model.item.CategoryItem import CategoryItem
from catalog.model.modelBase import Base
from pylons.decorators.cache import beaker_cache


class CategoryModel(object):
    #collection = Base.category_collection

    def _fetch(self, **kwargs):
        collection = Base.category_collection
        #global collection
        """
        where
        by
        direction
        limit
        page
        skip
        one
        order
        get_cursor
        """
        if  len(kwargs) == 0:
            result_set = []
            cursor = collection.find()
            for item in cursor:
                result_set.append(CategoryItem(item))
            return result_set

        #if all (k in kwargs for k in ("where","one")):#do not work
        if 'where' in kwargs and 'one' in kwargs:
            return CategoryItem(collection.find_one(kwargs['where']))

        if 'where' in kwargs:
            result = []
            cursor = collection.find(kwargs['where'])

        skip = 0 if not 'skip' in kwargs else kwargs['skip']
        cursor.skip(skip)

        limit = 20 if not 'limit' in kwargs else kwargs['limit']
        cursor.limit(limit)
                
        if 'page' in kwargs:
            cursor.skip(limit * (int(kwargs['page']) - 1))
        
        if kwargs.has_key('one'):
            return CategoryItem(collection.find_one())

        if 'order' in kwargs:
            direction = 1 if kwargs['order'] == asc else -1
            by = id if not kwargs['by'] else kwargs['by']

        result_set = []
        for item in cursor:
            result_set.append(CategoryItem(item))
        return result_set
    @staticmethod
    def get_path(self):
        result = [self]
        parent_id = self.parent_id
        while parent_id >= 0:
            parent = CategoryModel.get_by_id(parent_id)
            if parent.to_dict: result.insert(0,parent)
            parent_id = parent.parent_id
        return result


    @staticmethod
    def get_by_id(id):
        return CategoryModel._fetch(CategoryModel(),where={'id':id},one=True)

    @staticmethod
    def get_totals(constraint=None):
        collection = Base.site_collection
        if isinstance (constraint, dict):
            return collection.find(constraint).count()
        return collection.find().count()

    @staticmethod
    def get_by_slug(slug):
        return CategoryModel._fetch(CategoryModel(),where={'slug':slug}, one=True)


