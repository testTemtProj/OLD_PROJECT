# coding=utf-8
import logging
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from rynok.model.vendorsModel import VendorsModel
from rynok.model.referenceModel import ReferenceModel
from rynok.model.categoriesModel import CategoriesModel

from rynok.lib.base import BaseController, render

log = logging.getLogger(__name__)

class VendorController(BaseController):

    def index(self, vendor, cat_url, page):
        """
        Возвращает продукты данного производителя в зависимости от фильтров
        Входные параметры:
            vendor = * (string) - транслитиованное имя производителя
            cat_url = * (string) - категория в которой находятся товары производителя
            page = [0-9]+ (string) - текущая страница пейджинга
        Параметры запроса:
            m_id = [(int)] - массив id магазинов отмеченных в фильтре
            price_min = [0-9]+ (string) - минимальная цена отмеченная в фильтре
            price_max = [0-9]+ (string) - максимальная цена отмеченная в фильтре
            sort_by = rating | price | popular (string) - по какому полю сортировать
            sort_order = asc | desc (string) - порядок сортировки
            per_page = 10 | 25 | 50 (string) - количество товаров на странице
        Параметры шаблонизатора:
            c.vendor = {} (dict) - текущий производитель
            c.current_cat = None | {} (dict) - текущая категория (None когда находимся в корне)
            c.markets = [(int)] - массив id магазинов отмеченных в фильтре
            c.affordable_price = (int) - максимальная возможная цена в категории данного производителя
            c.price_min = (int) - минимальная цена выбранная в фильтре
            c.price_max = (int) - максимальная цена выбранная в фильтре
            c.sort_settings = {rating | price | popular (string) : desc | asc (string)} (dict) - текущие настройки сортировки для панели сортировки
            c.per_page = (int) - количество товаров на странице для панели сортировки
            c.page = (int) - текущая страница пейджинга
            c.current_url = * (string) - ссылка на данную страницу для формирования параметров
            c.query = {} (dict) - запрос для определения цены в фильтре цены
            c.currency = (string) - текущая валюта
        """

        vendors_model = VendorsModel
        reference_model = ReferenceModel
        categories_model = CategoriesModel
        c.error_message = None
        query = {}

        c.vendor = vendors_model.get_by_transformedTitle(vendor)
        if not c.vendor:
            return abort(status_code=404)
        query['vendor'] = c.vendor['id']

        c.current_cat = categories_model.getByURL(url = cat_url)
        if c.current_cat:
            query['categoryId'] = c.current_cat['ID']

        try:
            c.markets = json.loads(request.params.get('m_id', '[]'))
        except ValueError:
            print 'bad param m_id'
            c.markets = []

        if len(c.markets):
            query['shopId'] = {'$in':c.markets}

        c.currency = request.params.get('currency', 'UAH')
        c.query = query

        c.affordable_price =  int(reference_model.get_max_price(query, c.currency)) + 1

        query[c.currency] = {}
        c.price_min = int(request.params.get('price_min', 0))
        query[c.currency]['$gt'] = c.price_min

        c.price_max = request.params.get('price_max', None)
        if c.price_max:
            query[c.currency]['$lt'] = int(c.price_max)


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

        c.current_url = '/vendor/' + c.vendor['transformedTitle']
        if c.current_cat:
            c.current_url += c.current_cat['URL']
        c.current_url += '/' + page

        if (c.price_max and (int(c.price_max) > c.affordable_price)) or c.price_max is None:
            c.price_max = c.affordable_price
        keywords = []
        for product in c.products:
            keywords.append(product['title'].strip())

        c.meta_title = u'Рынок | Производитель — «%s»'%(c.vendor['name'])
        c.meta_keywords     = ', '.join(keywords)
        c.meta_description  = u'Рынок Yottos объединяет все интернет-магазины в одном месте, помогает покупателям найти самое выгодное предложение, а продавцам — заинтересованных клиентов.'
        return render('/vendor.mako.html')
