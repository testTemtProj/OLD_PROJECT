# coding: utf-8
import logging
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rynok.lib.base import BaseController, render
from rynok.model.marketsModel import MarketsModel
from rynok.model.referenceModel import ReferenceModel
from rynok.model.categoriesModel import CategoriesModel
from rynok.lib import helpers as h


log = logging.getLogger(__name__)

class MarketController(BaseController):

    def index(self, market, cat_url, page):
        markets_model = MarketsModel
        reference_model = ReferenceModel
        categories_model = CategoriesModel
        c.error_message = None    
        query = {}
        #c.market = markets_model.get_by_id(266)
        c.market = markets_model.get_by_transformedTitle(market)
        print c.market['transformedTitle']
        if not c.market:
            return abort(status_code=404)
        query['shopId'] = c.market['id']

        c.current_cat = categories_model.getByURL(url = cat_url)
        if c.current_cat:
            query['categoryId'] = c.current_cat['ID']

        try:
            c.vendors = json.loads(request.params.get('v_id', '[]'))
        except ValueError:
            print 'bad param v_id'
            c.vendors = []        
        if len(c.vendors):
            query['vendor'] = {'$in':c.vendors}

        c.currency = request.params.get('currency', 'UAH')
        c.query = query

        c.affordable_price =  int(reference_model.get_max_price(query, c.currency)) + 1

        query[c.currency] = {}
        c.price_min = int(request.params.get('price_min', 0))
        query[c.currency]['$gte'] = c.price_min

        c.price_max = request.params.get('price_max', None)
        if c.price_max:
            query[c.currency]['$lte'] = int(c.price_max)


        count_products = reference_model.get_count(query=query)

        sort_by = request.params.get('sort_by', 'price')
        if sort_by == 'rating':
            by = 'Rate'
        elif sort_by == 'price':
            by = c.currency
        elif sort_by == 'popular':
            by = 'popular'

        sort_order = request.params.get('sort_order', 'desc')
        c.sort_settings = {sort_by:sort_order}

        c.per_page = int(request.params.get('per_page', 10))
                
        if count_products > 0:
            c.products = reference_model.get_reference(where=query, perPage = c.per_page, page = int(page)-1, by=by, direction=sort_order)
        else:
            #get_less_products_query = query.copy()
            #get_less_products_query[c.currency] = {'$lt' : c.price_min}
            get_more_products_query = query.copy()
            del(get_more_products_query[c.currency])# = {'$lte' : c.price_max} 
            #less_products = reference_model.get_reference(where=get_less_products_query, limit=2, by=c.currency, direction=-1)
            #more_products = reference_model.get_reference(where=get_more_products_query, limit=2, by=c.currency, direction=1)
            #c.products = more_products
            print get_more_products_query
            c.products = reference_model.get_reference(where=get_more_products_query, perPage = c.per_page, page = int(page)-1, by=by, direction=sort_order)            
            c.error_message = u"По даной цене товары не найдены, показаны без учета цены"
            count_products = reference_model.get_count(query=get_more_products_query)
            
        c.page = page
        c.total_pages = count_products / c.per_page
        if count_products % c.per_page:
            c.total_pages +=1

        c.current_url = '/market/' + c.market['transformedTitle']
        if c.current_cat:
            c.current_url += c.current_cat['URL']
        c.current_url += '/' + page

        if (c.price_max and (int(c.price_max) > c.affordable_price)) or c.price_max is None:
            c.price_max = c.affordable_price
        
        if count_products <= 0:
            c.noresult = u"В данном ценовом диапазоне товары отсутствуют"
        else:
            c.noresult = ""        
                    
        return render('/market.mako.html')
