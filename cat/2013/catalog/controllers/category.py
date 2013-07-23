# coding=utf-8
import logging
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from catalog.lib.base import BaseController, render
from catalog.model.CategoryModel import CategoryModel
from catalog.model.item.CategoryItem import CategoryItem
from catalog.model.SiteModel import SiteModel
from catalog.model.item.SiteItem import SiteItem
from catalog.model.modelBase import Base
import catalog.lib.sphinxapi as sphinxapi
from urlparse import urlparse
from pprint import pprint
from pylons.i18n import get_lang, set_lang
from catalog.lib.base import *
import catalog.lib.helpers as h
import json
import datetime
import re
from pylons import cache
from beaker.cache import cache_regions, cache_region, region_invalidate
from pylons.decorators.cache import beaker_cache
from gettext import gettext as _
from pylons.decorators.cache import create_cache_key
from catalog.config.environment import load_environment

log = logging.getLogger(__name__)

class CategoryController(BaseController):

    def index(self, category="Main", page=1):
        c.lang = get_lang() 
        c.sites = []
        if not category:
            c.error = _("Sorry, there is no such category.")
            return redirect(url(controller="category", action="index"))

        c.category = CategoryModel.get_by_slug(category)
        c.site_name = str('name_'+c.lang[0])
        c.site_descr = str('description_'+c.lang[0])
        if c.category.id is None:
            c.error = _("Sorry, there is no such category.")
            c.category = CategoryModel.get_by_slug("Main")

        if int(c.category.is_leaf) == 1:
            c.sites = SiteModel.get_by_category(int(c.category.id),page,lang=c.lang)
            c.totals = CategoryModel().get_totals({'category_id':int(c.category.id)})
            c.pages = c.totals/20 + 1  if (c.totals/20) else c.totals/20
        c.cur_page = page
        c.slug = c.category.slug
        children = c.category.get_children()[1:]
        
        c.children = []
        for child in children:
            if re.search(u'[a-zA-Zа-яА-я]+', child[0].to_dict['title_'+c.lang[0]]):
                child[0].title = child[0].to_dict['title_'+c.lang[0]]
            if len(child)>0:
                for i in range(1,len(child)):
                    if re.search(u'[a-zA-Zа-яА-я]+', child[i][0].to_dict['title_'+c.lang[0]]):
                        child[i][0].title = child[i][0].to_dict['title_'+c.lang[0]]

            c.children.append(child)

        c.keywords = c.category.to_dict.get('keywords')
        c.description = c.category.to_dict.get('description')

        if re.search(u'[a-zA-Zа-яА-я]', c.category.to_dict['title_'+c.lang[0]]):
            c.category.title = c.category.to_dict['title_'+c.lang[0]]

        breadcrunchs = []
        if int(c.category.id) != 0:
            breadcrunchs =  CategoryModel.get_path(c.category)
        c.breadcrunchs = []
        for crunch in breadcrunchs:
            if re.search(u'[a-zA-Zа-яА-я]+', crunch.to_dict.get('title_'+c.lang[0],'')):
                crunch.title = crunch.to_dict['title_'+c.lang[0]]
            c.breadcrunchs.append(crunch)
        return render('/category/category.mako.html')



    def search(self,page=1):
        c.lang = get_lang() 
        c.site_name = str('name_'+c.lang[0])
        c.site_descr = str('description_'+c.lang[0])

        page = int(page) if int(page) > 0 else 1
        
        client = Base.sphinx_client

        client.SetMatchMode(sphinxapi.SPH_MATCH_EXTENDED2)
        client.SetLimits((page-1)*20,20)

        query = request.GET.get("q", "")
        result = client.Query(query, index='catalog')
        c.query = request.GET['q']

        if result is not None:
            if 'matches' not in result or not len(result['matches']):
                return render('/category/not_found.mako.html')

            c.cur_page = page
            
            temp = [item['id'] for item in result['matches']]
            c.matches = result['total']
            c.pages = c.matches/20 + 1  if c.matches % 20 else c.matches/20
            c.sites = SiteModel.get_by_id(temp)

            c.script = h.HTML.literal("<script type=\"text/javascript\"><!--\nyottos_advertise = \"6aafe89a-98ec-11e0-bbc7-00163e0300c1\";\n//--></script><script type=\"text/javascript\" src=\"http://cdn.yottos.com/getmyad/_a.js\"></script>")
            
            for site in c.sites:
                site.name_en = unicode(client.BuildExcerpts([site.name_en, ], 'catalog', query, opts={'allow_empty':False, 'limit':1024})[0], 'utf-8')
                site.name_uk = unicode(client.BuildExcerpts([site.name_uk, ], 'catalog', query, opts={'allow_empty':False, 'limit':1024})[0], 'utf-8')
                site.name_ru = unicode(client.BuildExcerpts([site.name_ru, ], 'catalog', query, opts={'allow_empty':False, 'limit':1024})[0], 'utf-8')
                site.description_en = unicode(client.BuildExcerpts([site.description_en, ], 'catalog', query, opts={'allow_empty':False, 'limit':1024})[0], 'utf-8')
                site.description_uk = unicode(client.BuildExcerpts([site.description_uk, ], 'catalog', query, opts={'allow_empty':False, 'limit':1024})[0], 'utf-8')
                site.description_ru = unicode(client.BuildExcerpts([site.description_ru, ], 'catalog', query, opts={'allow_empty':False, 'limit':1024})[0], 'utf-8')
        else: 
            return render('/category/not_found.mako.html')
        return render('/category/search.mako.html')
    
    @cache_region('short_term','tree')
    def tree(self):
        if not request.is_xhr:
            return abort(status_code=404)
        t = h.get_tree(lang=get_lang()[0])
        return h.HTML.literal(json.dumps(t["children"], ensure_ascii=False))
