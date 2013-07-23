# coding: utf-8
from rynok.model.baseModel import Base

class CategoriesModel(object):
    CategoriesCollection = Base.category_collection

    @staticmethod
    def getCategoryById(categoryId):
        return CategoriesModel.CategoriesCollection.find_one({"ID": categoryId}, slave_okay=True)

    @staticmethod
    def getByTranslitedName(translitedName):
        return CategoriesModel.CategoriesCollection.find_one({'Translited': str(translitedName)}, slave_okay=True)


    @staticmethod
    def getByURL(url):
        if not len(url):
            return None

        if url[0] != '/':
            url = '/'+url

        if url[len(url) - 1] == '/':
            url = url[0:len(url) - 1]

        return CategoriesModel.CategoriesCollection.find_one({"URL": url}, slave_okay=True)

    @staticmethod
    def getBannerByURL(url):
        """Возвращает баннер по урлу категории
        Входные параметры url - урл категории
        Возращает баннер из базы, или пустую строку        
        """
        banner = CategoriesModel.getByURL(url=url)['baner']
        if banner is None:
            return ""
        else:
            return banner
        
    @staticmethod
    def getCategoryIdByName(categoryName):
        return CategoriesModel.CategoriesCollection.find_one({"Name": str(categoryName)}, slave_okay=True).get("ID", False)

    @staticmethod
    def getChildrens(categoryId, non_empty=False):
        query = {}
        query['ParentID'] = categoryId
        if non_empty:
            query['count'] = {'$gt':0}
        return CategoriesModel.CategoriesCollection.find(query, slave_okay=True).sort('Name', 1)

    @staticmethod
    def getParentCategory(categoryId):
        category = CategoriesModel.CategoriesCollection.find_one({"ID":categoryId}, slave_okay=True)
        return CategoriesModel.CategoriesCollection.find_one({"ID":category['ParentID']}, slave_okay=True)

    @staticmethod
    def getAll():
        return CategoriesModel.CategoriesCollection.find(slave_okay=True)

    @staticmethod
    def getCategoriesByParentId(parentId, limit=False):
        request = CategoriesModel.CategoriesCollection.find({'ParentID': parentId, 'count':{'$gt': 0}}, slave_okay=True).sort('Name', 1)
        if limit:
            request.limit(limit)
        return request

    @staticmethod
    def getByTranslitedTitle(title, parentId=None):
        where = {}
        if parentId:
            where = {"Translited" : str(title), "ParentID" : int(parentId)}
        else:
            where = {"Translited" : str(title)}

        return CategoriesModel.CategoriesCollection.find_one(where, slave_okay=True)
        
    @staticmethod
    def get_last_category(url):
        splited = url.split('/')
        category = None
        parent_id = 0
        for title in splited:
            if title == "":
                break
            category = CategoriesModel.getByTranslitedTitle(title=title, parentId=parent_id)
            if category is not None:
                parent_id = category['ID']
            else:
                return None
        return category

    @staticmethod
    def get_popular(limit, count_products):
        return CategoriesModel.CategoriesCollection.find({'isLeaf': True, 'count':{'$gt': count_products}}, slave_okay=True).sort('popularity', -1).limit(limit)

    @staticmethod
    def get_by_ids(ids):
        if not isinstance(ids, list):
            raise Exception('ids must be list')
        return CategoriesModel.CategoriesCollection.find({'ID':{'$in':ids}}, slave_okay=True)
