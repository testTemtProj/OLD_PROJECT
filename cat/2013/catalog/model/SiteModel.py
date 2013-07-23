from catalog.model.item.SiteItem import SiteItem
from catalog.model.modelBase import Base
from catalog.lib.celery.tasks import check_url
from datetime import date
import pymongo

class SiteModel(object):
    @staticmethod
    def _fetch(**kwargs):
        collection = Base.site_collection
        """
        where {key:value}
        by
        direction
        limit int
        page int
        skip int
        one bool
        order 
        get_cursor
        in {field:{$in:[values_arr]}}
        """
        if  len(kwargs) == 0:
            result_set = []
            cursor = collection.find()
            for item in cursor:
                result_set.append(SiteItem(item))
            return result_set


        if 'where' in kwargs and 'one' in kwargs:
            return SiteItem(collection.find_one(kwargs['where']))

        if 'where' in kwargs:
            result = []
            cursor = collection.find(kwargs['where'])


        if 'lang' in kwargs:
            if kwargs['lang'] in ['ru','en','uk']:
                sort_name_lang = 'name_'+kwargs['lang']
                cursor.sort(sort_name_lang, direction=pymongo.ASCENDING)
 
        skip = 0 if not 'skip' in kwargs else kwargs['skip']
        cursor.skip(skip)

        limit = 20 if not 'limit' in kwargs else kwargs['limit']
        cursor.limit(limit)
                
        if 'page' in kwargs:
            cursor.skip(limit * (int(kwargs['page']) - 1))
        
        if kwargs.has_key('one'):
            return SiteItem(collection.find_one())

        if 'order' in kwargs:
            direct = 1 if kwargs['order'] == "asc" else -1
            by = "id" if not kwargs['by'] else kwargs['by']
            cursor.sort(by,direction=direct)


        result_set = []
        for item in cursor:
            result_set.append(SiteItem(item))
        return result_set


    def save(self,site):
        new_site = {}
        for k,v in site.iteritems():
            new_site[str(k)]=str(v)
        er = SiteItem(new_site)
        er.save()


    @staticmethod
    def get_by_title(title):
        return SiteModel._fetch(where={'title':title},page=1)
    
    @staticmethod
    def get_by_category(category_id,page=1,lang="ru"):
        return SiteModel._lang_fetch(where={'$and':[{'category_id':category_id}, {'checked':True}, {'avaible':True}]},page=page, lang=lang)  


    @staticmethod
    def get_by_id(id):
        return [SiteModel._fetch(where={'id': site_id}, one=True) for site_id in id] if isinstance(id, list) else SiteModel._fetch(where={'id':id},one=True)

    @staticmethod
    def _lang_fetch(**kwargs):
        result = []

        kwargs['where']["name_"+kwargs['lang'][0]] = ""
        curs = SiteModel._fetch(**kwargs)
        kwargs['where']["name_"+kwargs['lang'][0]] = {"$ne" : ""} 
        curs1 = SiteModel._fetch(**kwargs)
        for row in curs1: result.append(row)
        for row in curs: result.append(row)
        return result
