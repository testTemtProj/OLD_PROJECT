# coding: utf-8
from rynok.lib.base import BaseController, render
from pylons import request, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from rynok.lib import sphinxapi

import json
from rynok.model.referenceModel import ReferenceModel
from rynok.model.vendorsModel import VendorsModel
from rynok.model.categoriesModel import CategoriesModel
from rynok.model.settingsModel import SettingsModel
import re
import urllib
class SearchController(BaseController):
    """
    Контроллер поиска товаров
    """
    def _search(self, query):
        
        sphinx = sphinxapi.SphinxClient()
        sphinx.SetFieldWeights({"title":30})
        sphinx.SetFieldWeights({"vendor":20})
        sphinx.SetFieldWeights({"category":10})
        sphinx.SetFieldWeights({"description":1})
        
        return sphinx.Query("* "+unicode(query)+" *")
        
    def index(self, cat_url, page):
        """
        Главный экшн поиска 
        параметр 'query'
        Входные параметры:
            page - текущая страница пейджинга
            cat_url - текущая категория
        Параметры запроса:
            m_id - массив выбранных магазинов в фильтре
            v_id - массив выбранных производителей в фильтре
            price_min - минимальная цена в фильтре
            price_max = максимальная цена в фильтре
            sort_by - по какому полю сортировать
            sort_order - направление сортировки
            per_page - количество товаров на странице
            currency - валюта, в которой отобразаются товары
            query - строка поискового запроса
        Параметры шаблонизатора:
            c.current_cat - текущая категория
            c.markets - отмеченные магазины
            c.vendors - отмеченные производители
            c.affordable_price - максимальная возможная цена по выбранным параметрам
            c.price_min - минимальная выбранная цена
            c.price_max - максимальная выбранная цена
            c.sort_settings - выбранные параметры сортировки
            c.page - номер текущая страница пейджинга
            c.per_page - выбранное количество товаров на странице
            c.price_query - запрос для определения цены в фильтре
            c.currency - текущая валюта
            c.find - то что вы искали
            c.noresult - показывает 
        """

        c.find = unicode(request.params.get('query', ""))
        if not c.find:
            c.find = " "
        referer = request.headers.get('Referer', '')
        http_host = request.environ.get('HTTP_HOST')
        c.back_url = referer
        if referer.find(http_host) == -1:
            c.back_url = '/'
            
        if not len(c.find):
            return abort(status_code=404)
        
        sphinx_result = self._search(c.find)
        
        if sphinx_result is None:
            c.cats = self._get_popular_categories()
            return render('noresults.mako.html')

        search_result = sphinx_result['matches']
        

        if not len(search_result):
            c.cats = self._get_popular_categories()
            return render('noresults.mako.html')
        c.search_query = '?query=%s' % (c.find)
        categories_model = CategoriesModel()

        ids = []
        c.all_markets = set()
        c.all_vendors = set()
        c.cats = set()
        query = {}        
        for result_item in search_result:
            ids.append(result_item['id'])
            c.all_markets.add(result_item['attrs']['shopid'])
            if result_item['attrs']['vendor_attr']>0:
                c.all_vendors.add(result_item['attrs']['vendor_attr'])
            c.cats.add(result_item['attrs']['categoryid'])
        c.cats = list(c.cats)        
        c.all_vendors = list(c.all_vendors)
        c.all_markets = list(c.all_markets)
        query['id_int'] = {'$in':ids}

        c.current_cat = categories_model.getByURL(url = cat_url)
        if c.current_cat:
            query['categoryId'] = c.current_cat['ID']

        try:
            c.markets = json.loads(request.params.get('m_id', '[]'))
            if len(c.markets):
                query['shopId'] = {'$in':c.markets}
        except ValueError:
            print 'bad param m_id'
            c.markets = []


        try:
            c.vendors = json.loads(request.params.get('v_id', '[]'))
            if len(c.vendors):
                query['vendor'] = {'$in':c.vendors}
        except ValueError:
            print 'bad param v_id'
            c.vendors = []

        c.currency = request.params.get('currency', 'UAH')
        c.price_query = query

        c.affordable_price = int(ReferenceModel.get_max_price(query, c.currency)) + 1
        
        query[c.currency] = {}
        c.price_min = int(request.params.get('price_min', 0))
        query[c.currency]['$gt'] = c.price_min
        
        c.price_max = request.params.get('price_max', None)
        if c.price_max:
            query[c.currency]['$lt'] = int(c.price_max)
        count_products = ReferenceModel.get_count(query=query)
        
        if count_products == 0:
            c.find = c.find.encode('utf-8')
            _url = '/search/?query='+urllib.quote(c.find, '/')
            session['noresult']=True
            print session
            session.save()
            return redirect(_url, 301)
            c.cats = self._get_popular_categories()
            return render('/noresults.mako.html')
                
        print session
        sort_by = request.params.get('sort_by', 'price')
        sort_order = request.params.get('sort_order', 'desc')
        
        c.per_page = int(request.params.get('per_page', 10))
        
        if sort_by == 'rating':
            by = 'Rate'
        elif sort_by == 'price':
            by = c.currency
        elif sort_by == 'popular':
            by = 'popular'
        else:
            by = 'price'
        c.products = []        
        c.sort_settings = {sort_by:sort_order}  
        c.page = page
        c.total_pages = count_products / c.per_page
        if count_products % c.per_page:
            c.total_pages += 1

        c.current_url = "/search"
        if c.current_cat:
            c.current_url += c.current_cat['URL']
        c.current_url += "/" + page

        if (c.price_max and (int(c.price_max) > c.affordable_price)) or c.price_max is None:
            c.price_max = c.affordable_price

        keywords = []
        for product in c.products:
            keywords.append(product['title'].strip())

        c.meta_title        = u'Рынок | Результаты поиска — «%s»'%(c.find)
        c.meta_keywords     = ', '.join(keywords)
        c.meta_description  = u'Рынок Yottos объединяет все интернет-магазины в одном месте, помогает покупателям найти самое выгодное предложение, а продавцам — заинтересованных клиентов.'
        c.banner = SettingsModel.get_search_page_banner()
        
        #TODO сделать нормальную проверку
        if len(request.params)==1 and c.current_cat is None:                                    
            for product_id in ids[(int(page)-1)*c.per_page:(int(page))*c.per_page]:
                product = ReferenceModel.get_reference(where={'id_int': product_id}, one=True)
                if product:
                    c.products.append(product)                                    
            c.sort_settings = {'price':sort_order}        
        else:
            c.products = ReferenceModel.get_reference(where=query, perPage=c.per_page, page=int(page)-1, by=by, direction=sort_order)
            
        if 'noresult' in session and session['noresult']:
            c.noresult = u"По предыдущему запросу товары не найдены, показанны все результаты"
        else:
            c.noresult = ""
                    
        session['noresult'] = False
        session.save()
        
        return render('/search.mako.html')

        
    def _get_popular_categories(self):
        categories_model = CategoriesModel
        cats = categories_model.getChildrens(categoryId=0, non_empty=True)
        categories = []
        for cat in cats:
            categories.append(cat)
        return categories
