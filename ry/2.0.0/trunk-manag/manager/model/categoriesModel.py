# coding: utf-8
from manager.model.baseModel import Base
from manager.lib import helpers as h

class CategoriesModel():
    db = Base.connection
    categories_collection = Base.categories_collection


    @staticmethod
    def get_by_id(id):
        return CategoriesModel.categories_collection.find_one({"ID": id})


    @staticmethod
    def get_all():
        result = []
        categories = CategoriesModel.categories_collection.find().sort([('ParentID', 1),('Name', 1)])
        
        for category in categories:
            result.append(category)

        return result

        
    @staticmethod
    def getChildrens(categoryId):
        categories = []

        for currentCategory in CategoriesModel.categories_collection.find({"ParentID": categoryId}):
            categories.append(currentCategory)

        return categories


    @staticmethod
    def has_children(category_id):
        if CategoriesModel.categories_collection.find({"ParentID": category_id}).count():
            return True
        return False


    @staticmethod
    def get_by_parent_id(parentId, empty=True):
        categories = []
        query = {}
        query['ParentID'] = parentId
        if not empty:
            query['count'] = {'$gt': 0}

        for x in CategoriesModel.categories_collection.find(query):
            categories.append(x)

        return categories
    

    @staticmethod
    def reparent(node_id, parent_id):
        category = CategoriesModel.categories_collection

        changes = {
            'ParentID': parent_id
        }

        category.update({'ID': node_id}, {'$set': changes}, upsert=True)
        
        return 1


    @staticmethod
    def rename(id, newName):
        coll = CategoriesModel.categories_collection
        cat = coll.find_one({'ID': id})
        doc = {
            'ID': id,
            'Name': newName,
            'ParentID': cat['ParentID'],
            'URL': cat['URL'],
            'Translited': h.translate(newName),
            '_id': cat['_id']
        }

        if cat.has_key('Description'):
            doc['Description'] = cat['Description']

        if cat.has_key('Title'):
            doc['Title'] = cat['Title']

        if cat.has_key('MetaKey'):
            doc['MetaKey'] = cat['MetaKey']

        coll.update({'ID': id}, doc, upsert=True)
        
        return 'ok'


    @staticmethod
    def change(params):
        coll = CategoriesModel.categories_collection
        cat = coll.find_one({'ID': params['ID']})
        coll.update(
                {'ID': params['ID']},
                {'$set': {'Name': params['Name'],
                          'AlternativeTitle' : params['AlternativeTitle'] if len(params['AlternativeTitle']) < 15 else '',
                          'Translited': h.translate(params['Name']),
                          'banner': params['Baner'],
                          'Description': params['Description'],
                          'Title': params['Title'],
                          'MetaKey': params['MetaKey']
                }},
                upsert=True
        )
        
        return 'ok'


    @staticmethod
    def remove(id):
        collection = CategoriesModel.categories_collection
        category = collection.find_one({'ID': id})

        # Если категории не существует
        if category is None:
            return False

        # Установить isLeaf для родительской категории, если из неё удален последний элемент
        if collection.find({'ID': category['ParentID']}).count() == 0:
            collection.update({'ID': int(category['ParentID'])}, {'$set': {'isLeaf': True}})

        # Удалить вложенные категории
        for remove_cat in CategoriesModel.getChildrens(categoryId=id):
            collection.remove({'ID': remove_cat['ID']})

        collection.remove({'ID': id})
        return True


    @staticmethod
    def save(params):
        categories = CategoriesModel.categories_collection
        params['ID'] = categories.find().sort('ID', -1).limit(1).next()['ID'] + 1

        if len(params['Name']) < 1:
            params['Name'] = unicode(params['ID'])
            params['Translited'] = unicode(params['ID'])

        categories.insert({
            'ID':           params['ID'],
            'Name':         params['Name'],
            'Translited':   h.translate(params['Name']),
            'count':        0,
            'banner':       params['Baner'],
            'URL':          params['URL'],
            'ParentID':     int(params['ParentID']),
            'Description':  params['Description'],
            'Title':        params['Title'],
            'AlternativeTitle' : params['AlternativeTitle'] if len(params['AlternativeTitle']) < 15 else '',
            'isLeaf':       True,
            'MetaKey':      params['MetaKey']
        })
        
        categories.update({'ID': int(params['ParentID'])}, {'$set': {'isLeaf': False}})

        return params
