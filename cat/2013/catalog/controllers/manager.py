import logging
import base64


from pylons.i18n import get_lang, set_lang
from catalog.controllers.category import CategoryController
from catalog.model.CategoryModel import CategoryModel
from catalog.model.item.CategoryItem import CategoryItem
from catalog.model.SiteModel import SiteModel
from catalog.model.item.SiteItem import SiteItem
import catalog.lib.helpers as h
import json
import datetime
from beaker.cache import cache_regions, cache_region, region_invalidate
import pymongo
import re
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from catalog.lib.auth import auth
from catalog.lib.auth import add_user, rem_user, upd_user
from catalog.model.SiteModel import SiteModel
from catalog.model.item.SiteItem import SiteItem
from catalog.model.CategoryModel import CategoryModel
from catalog.model.modelBase import Base
from catalog.lib.base import BaseController, render
import hashlib

log = logging.getLogger(__name__)

class ManagerController(BaseController):
    filter = []

    @auth
    def index(self):

        return render('/manager/manager.mako.html')

    def login(self):
        return render('/manager/login.mako.html') 

    def dologin(self):
        if not request.POST:
            return redirect(url(controller='manager', action='login'))
        uname = request.POST['user_name']
        response.set_cookie('logins', base64.b64encode(unicode(uname).encode('utf-8')) + ':' + hashlib.md5(request.POST.get('password')).hexdigest(), max_age=36000)
        return redirect('/manager/index')

    @auth
    def logout(self):
        response.set_cookie('logins', "")
        return redirect('/manager/login')

    @auth
    def sites(self, category_id=0,start=0, limit=10):
        if not request.is_xhr:
            return abort(status_code=404)
        start = request.params.get('start',0)
        limit = request.params.get('limit',10)
        return h.HTML.literal(json.dumps(h.get_sites(int(category_id),int(start),int(limit))))

    @auth
    def get_category(self):
        if not request.is_xhr:
            return abort(404)
        cat = CategoryModel().get_by_id(int(request.params['id']))
        if '_id' in vars(cat): del vars(cat)['_id'] 
        return h.HTML.literal(json.dumps({"category":[vars(cat)]}))

    @auth
    def save_category(self):
        if not request.is_xhr:
            return abort(404)
        region_invalidate(CategoryController().tree, 'tree_cache', 'tree')
        category = dict(request.POST)
        category['is_leaf'] = 1 if 'is_leaf' in category else 0
        category['id'] = int(category['id']) 
        category['parent_id'] = int(category['parent_id']) if category['id'] != 0 else ''
        CategoryItem(category).save()
        pass

    @auth
    def save_site(self):
        if not request.is_xhr:
            return abort(404)
        site = dict(request.POST)
        site['id'] = int(site['id'])
        site['category_id'] = int(site['category_id'])
        site['rate'] = int(site.get('rate',0)) if site.get('rate',0) else 0
        site['checked'] = True if site.get('checked',False) == "true" else False
        site['avaible'] = True if site.get('avaible',False) == "true" else False
        SiteItem(site).update()
        pass

    @auth
    def get_leaf_categories(self):
        if not request.is_xhr:
            return abort(404)
        return h.HTML.literal(json.dumps({"leafs":h.get_leafs()}))

    @auth
    def set_filter_sites(self):
        global filter
        if not request.is_xhr:
            return abort(404)

        tday = datetime.date.today()

        search_params = dict(request.POST)
        search_params['checked'] = True if search_params.get('checked') else False 
        search_params['avaible'] = True if search_params.get('avaible') else False
        sdate = datetime.datetime(int(search_params.get("date_add_start").split('-')[2]),\
                                      int(search_params.get("date_add_start").split('-')[1]),\
                                      int(search_params.get("date_add_start").split('-')[0])) if search_params.get("date_add_start",'') != '' else datetime.datetime(1970, 1, 1)
        edate =  datetime.datetime(int(search_params.get("date_add_end").split('-')[2]),\
                                      int(search_params.get("date_add_end").split('-')[1]),\
                                      int(search_params.get("date_add_end").split('-')[0])) if search_params.get("date_add_end",'') != '' else datetime.datetime.today()
        search_params['date_add'] = {"$gte": sdate, "$lte": edate}

        del search_params['date_add_start']
        del search_params['date_add_end']

        params = []
        for param in search_params.keys(): 
            if search_params[param] == '':
                del search_params[param]
            else:
                params.append({param:search_params[param]})
        filter = params

        return h.HTML.literal(json.dumps({'success':True}))

    @auth
    def get_filter_sites(self, start=0, limit=10):
        global filter

        start = int(request.params.get('start',0))
        limit = int(request.params.get('limit',10))

        sites = h.get_filtered_sites(filter,start=start,limit=limit)
        return h.HTML.literal(json.dumps(sites))

    @auth
    def add_category(self):
        if not request.is_xhr:
            return abort(404)
        region_invalidate(CategoryController().tree, 'tree_cache', 'tree')
        category = dict(request.POST)
        category['is_leaf'] = 1 if 'is_leaf' in category else 0
        category['parent_id'] = int(category['parent_id'])
        del category['id']
        CategoryItem(category).save()
        pass

    @auth
    def del_category(self):
        if not request.is_xhr:
            return abort(404)

        region_invalidate(CategoryController().tree, 'tree_cache', 'tree')
        category = dict(request.POST)
        CategoryItem(category).delete()

    @auth
    def del_site(self):
        if not request.is_xhr:
            return abort(404)

        site = dict(request.POST)
        SiteItem(site).delete()

    @auth
    def new_site_id(self):
        if not request.is_xhr:
            return abort(404)

        collection = Base.site_collection
        return h.HTML.literal(json.dumps({'id': (1 + int(collection.find().sort('id', pymongo.DESCENDING)[0]['id']))}))

    @auth
    def add_usr(self):
        user = dict(request.POST)
        if 'is_adm' in user: 
            user['is_adm'] = True if user['is_adm'] == 'on' else False
        else: 
            user['is_adm'] = False

        add_user(user)
        return 

    @auth
    def rem_usr(self):
        user = dict(request.POST)
        rem_user(user["user_name"])
        return 

    @auth
    def upd_usr(self):
        user  = dict(request.POST)

        if 'is_adm' in user: 
            user['is_adm'] = True if user['is_adm'] == 'on' else False
        else: 
            user['is_adm'] = False

        upd_user(user)
        return 

    @auth
    def get_rights(self):
        col = Base.users
        uname = request.cookies.get('logins').split(':')[0]
        user =  col.find_one({'user_name':base64.b64decode(uname)})
        return h.HTML.literal(json.dumps({'success': True, 'is_adm': user['is_adm']}))

    @auth
    def tree(self):
        if not request.is_xhr:
            return abort(status_code=404)
        t = h.get_tree(lang=get_lang()[0])
        return h.HTML.literal(json.dumps(t["children"], ensure_ascii=False))
