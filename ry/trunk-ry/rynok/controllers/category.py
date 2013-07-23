#coding: utf-8
""" Category Controller
"""
import logging
import rynok.lib.helpers as h
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from webhelpers.html.builder import HTML

from rynok.lib.base import BaseController, render
from rynok.model.categoriesModel import CategoriesModel
from rynok.lib import helpers as h
from rynok.model.referenceModel import ReferenceModel
from rynok.model.settingsModel import SettingsModel

LOG = logging.getLogger(__name__)

class CategoryController(BaseController):


    def __init__(self):
        BaseController.__init__(self)
        self.categories_model = CategoriesModel

    def index(self, url):
        category = self.categories_model.getByURL(url=url)
        if not category:
            return render('/error/error.mako.html')

        if 'isLeaf' in category and category['isLeaf']:
            return self.view(category=category)

        cats = self.categories_model.getChildrens(category["ID"], non_empty=True)
        c.cats = []
        for cat in cats:
            c.cats.append(cat)

        c.category = category
        return render('/category.mako.html')

    def all(self):
        cats = self.categories_model.getChildrens(categoryId=0, non_empty=True)
        c.cats = []
        for cat in cats:
            c.cats.append(cat)
        return render('/all.categories.mako.html')

    def popular(self):
        reference_model = ReferenceModel
        settings = SettingsModel.get_popular_block_settings()
        c.title = 'Популярные товары'
        c.products = reference_model.get_popular_products(settings['categories'], settings['per_category'])
        return render('/products.html')

    def new(self):
        reference_model = ReferenceModel
        c.title = 'Новые товары'
        c.products = reference_model.get_new_products(28)
        return render('/products.html')
    
    def view(self, category, page=1):
        reference_model = ReferenceModel
        if not isinstance(category, dict):
            category = self.categories_model.getByURL(category)
        c.category = category
        c.error_message = None

        sort_by = request.params.get('sort_by', 'price')
        if sort_by == 'rating':
            by = 'Rate'
        elif sort_by == 'price':
            by = 'price'
        elif sort_by == 'popular':
            by = 'popular'

        try:
            c.markets = json.loads(request.params.get('m_id', '[]'))
        except ValueError:
            c.markets = []

        try:
            c.vendors = json.loads(request.params.get('v_id', '[]'))
        except ValueError:
            c.vendors = []

        sort_order = request.params.get('sort_order', 'desc')

        try:
            c.price_min = int(request.params.get('price_min', 0))
        except:
            c.price_min = 0

        try:
            c.perPage = int(request.params.get('per_page', 10))
        except:
            c.perPage = 10

        c.currency = request.params.get('currency', 'UAH')

        query = {'categoryId':int(category['ID']), c.currency: {'$gt': c.price_min-1}}

        c.affordable_price = reference_model.get_max_price(query, c.currency) + 1
        c.price_max = int(request.params.get('price_max', c.affordable_price))

        query[c.currency]['$lt'] = c.price_max + 1


        if len(c.markets) > 0 and len(c.vendors) > 0:
            query['shopId'] = {'$in':c.markets}
            query['vendor'] = {'$in':c.vendors}

        if len(c.markets) > 0 and len(c.vendors) == 0:
            query['shopId'] = {'$in':c.markets}

        if len(c.markets) == 0 and len(c.vendors) > 0:
            query['vendor'] = {'$in':c.vendors}

        count_products = reference_model.get_count(query=query)

        """
        if count_products == 0:
            referer = request.headers.get('Referer', '')
            http_host = request.environ.get('HTTP_HOST')
            c.back_url = referer
            if referer.find(http_host) == -1:
                c.back_url = '/'

            cats = self.categories_model.getChildrens(categoryId=0, non_empty=True)
            c.cats = []
            for cat in cats:
                c.cats.append(cat)
                   
            c.noresult = u"По даной цене товары не найдены"
        
            return render('/empty.category.mako.html')
        """

        if count_products > 0:
            c.products = reference_model.get_reference(where=query, perPage = c.perPage, page = int(page)-1, by=by, direction=sort_order)
        else:
            #get_less_products_query = query.copy()
            #get_less_products_query[c.currency] = {'$lt' : c.price_min}
            get_more_products_query = query.copy()
            del(get_more_products_query[c.currency])# = {'$lte' : c.price_max} 
            #less_products = reference_model.get_reference(where=get_less_products_query, limit=2, by=c.currency, direction=-1)
            #more_products = reference_model.get_reference(where=get_more_products_query, limit=2, by=c.currency, direction=1)
            #c.products = more_products
            print get_more_products_query
            c.products = reference_model.get_reference(where=get_more_products_query, perPage = c.perPage, page = int(page)-1, by=by, direction=sort_order)            
            c.error_message = u"По даной цене товары не найдены, показаны без учета цены"
            count_products = reference_model.get_count(query=get_more_products_query)

        c.page = page

        c.total_pages = count_products/c.perPage
        if count_products%c.perPage:
            c.total_pages += 1

        c.sort_settings = {sort_by: sort_order}
        c.current_url = category['URL']+'/'+str(page)

        return render('/view.category.mako.html')
