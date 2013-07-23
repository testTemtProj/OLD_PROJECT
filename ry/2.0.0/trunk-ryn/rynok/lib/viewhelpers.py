# coding: utf-8
from pprint import pprint

from rynok.lib.base import render
from webhelpers.html import HTML
from pylons import url, request 
from beaker.cache import cache_region
from rynok.lib import helpers as h
from pylons import tmpl_context as c
from rynok.model.categoriesModel import CategoriesModel
from rynok.model.referenceModel import ReferenceModel
from rynok.model.item.referenceItem import ReferenceItem
from rynok.model.vendorsModel import VendorsModel 
from rynok.model.marketsModel import MarketsModel 
from rynok.model.staticPagesModel import StaticPagesModel
from rynok.model.settingsModel import SettingsModel
from pylons import app_globals
from datetime import datetime
import re
import urllib
import json
import math

def thumb_image(product):
    IMAGE_SIZES = {'thumb':'100x110',
                   'small':'128x80',
                   'big':'213x168',
                   'full':'800x700',
                   'orig':'orig'}
    images = {}
    for size in IMAGE_SIZES:
        images[size] = {
            'cdn':'',
#            'market':''
        }

        if product.images:
            images[size]['cdn'] = "%s/images/%s/%s" % (app_globals.cdnt, IMAGE_SIZES[size], product.images)

#        if product.picture:
#            images[size]['market'] = product.picture

    return images

def meta(type, category):
    type_list = {'title':'Title',
                 'keywords':'MetaKey',
                 'description':'Description'}
    try:
        result = category[type_list[type]]
    except BaseException, e:
        result = ''
    return result


def products(sort):
    settings = SettingsModel.get_popular_block_settings()
    reference_model = ReferenceModel

    c.sort = sort

    if sort == 'popular':
        selected_products = reference_model.get_popular_products(settings['categories'], settings['per_category'])
        c.title = u'Популярные товары'
        c.link = '/popular'
        c.additional_class = ''
    elif sort == 'new':
        selected_products = reference_model.get_new_products(28)
        c.title = u'Новые товары'
        c.link = '/new'
        c.additional_class = 'new'


    products = []
    scripts = []
    slider = []

    last_counter = 0

    for product in selected_products:
        currency = product['currencyId']
        if product[currency] > 0:

            price = math.modf(round(product[currency], 2))
            if price[0]==0:
                _price = str(int(price[1]))
            else:
                _price = str(int(price[1])) + '.' + str(price[0])[2:4]

            if currency == 'UAH':
                _price = u'%s грн' % _price
            elif currency == 'USD':
                _price = u'&#36; %s' % _price
            elif currency == 'EUR':
                _price = u'&euro; %s' % _price
            elif currency == 'RUB':
                _price += u' руб.'
        else:
            _price = ''
            
        if not product['counter']:
            product['counter'] = 0
            product['category'] = ''
        
        if last_counter != product['counter']:
            if len(product['category'])>20:
                name_category = product['category'][:20]+".."
            else:
                name_category = product['category']
            slider.extend(['<span class="slider-lb slider-lb%s">%s</span>' % (product['counter'], name_category)])
            last_counter = product['counter']

        images = thumb_image(product)

        image_links = ''
        for size in images:
            image_links += '<script type="thumb" id="item-%s-%s">' % (size, product['id'])
            image_counter = 0
            for type in images[size]:
                if images[size][type]:
                    if image_counter>0:
                        image_links += '\n'
                    image_counter += 1
                    image_links += images[size][type].lstrip('cmowz.')
            image_links += '</script>\n'
            
        product = '''
            <li unselectable="on" class="group%s">
                <a href="%s" class="product-link" id="product-%s" title="%s"
                   target="_blank" unselectable="on">
                   <span class="thumb">
                       <img id="item-%s" class="image-file" new="true" src="/img/no-photo.png" alt="%s">
                   </span>
                   <span class="price">%s</span>
                   <span class="title">%s</span>
                   </a>
            </li>
        ''' % (product['counter'], make_product_url(product), product['id'], product['title'], product['id'], product['title'], _price, product['title'])

        products.extend(product)
        scripts.extend(image_links)
        

    c.slider = ''.join(slider)

    c.products = ''.join(products)
    c.scripts = ''.join(scripts)

    return render('/view/blocks/products.html')

def banner_block(banner=''):
    return h.literal('<div class="banner">%s</div><div class="clr"></div>' % banner)

# кешировать бейкером HTML по входным параметрам
def categories(root, deep=1, show_count=True):
    if isinstance(root, dict):
        cats = h.get_categories(root["ID"], deep)
        root_cat = root
    else:
        cats = h.get_categories(root, deep)
        categories_model = CategoriesModel
        root_cat = categories_model.getCategoryById(root)
    c.root_title = root_cat["Name"]
    c.root_url = root_cat["URL"]+'/'
    c.cats = cats
    c.root_count = root_cat['count']
    c.show_count = show_count
    return render('/view/categories.mako.html')

#@cache_region('short_term', 'vendors_block')
def vendors():
    first_letter = ''
    c.vendors = []
    digits = set(['1','2','3','4','5','6','7','8','9','0','@', ' '])

    vendors = h.get_vendors()
    
    c.vendors_show_arrows = True
    if vendors.count() < 26:
        c.vendors_show_arrows = False

    for vendor in vendors:
        try:
            url = ''.join(['/vendor/', vendor['transformedTitle'], '/'])
            id = ''
            if vendor['name'][0] != first_letter:
                first_letter =  vendor['name'][0]
                if first_letter in digits:
                    id = ' id="DIGITS"'
                else:
                    id = ''.join([' id="', first_letter, '"'])
            c.vendors.extend(['<li', id, '><a href="', url, '">', vendor['name'], '</a></li>'])
        except KeyError, e:
            print '%s key in vendors does not exists, viewhelpers.py in vendors() ' % e
    
    c.vendors = ''.join(c.vendors)

    c.markets = []
    first_letter = ''
    
    
    markets = h.get_markets() 

    c.markets_show_arrows = True
    if markets.count() < 26:
        c.markets_show_arrows = False
    
    for market in markets:
        try:
            title = market['title'].lower()
            url = ''.join(["/market/", market['transformedTitle'], "/"])
            id = ''
            if market['title'][0] != first_letter:
                first_letter = market['title'][0]            
                if first_letter in digits:
                    id = ' id="SHOP_DIGITS"'
                else:
                    id = ''.join([' id="SHOP_', first_letter, '"'])
            c.markets.extend(['<li', id, '><a href="', url, '">', title, '</a></li>'])
        except KeyError, e:
            print '%s key in markets does not exists, viewhelpers.py in vendors() ' % e
    
    c.markets = ''.join(c.markets)

    c.vendors = HTML.literal(c.vendors)
    c.markets = HTML.literal(c.markets)
    return render('/view/blocks/vendors.mako.html')

def vendors_list():
    c.vendors = []
    vendors = VendorsModel.get_all()#h.get_vendors()
    
    for vendor in vendors:
        try:
            url = ''.join(['/vendor/', vendor['transformedTitle'], '/'])
            id = ''
            c.vendors.extend(['<li', id, '><a href="', url, '">', vendor['name'], '</a></li>'])
        except KeyError, e:
            print '%s key in vendors does not exists, viewhelpers.py in vendors() ' % e
    c.vendors = ''.join(c.vendors)

    c.vendors = HTML.literal(c.vendors)

    return render('/view/blocks/vendors.list.mako.html')
    
def basket():
    return render('/view/blocks/basket.mako.html')
    
def compare():
    return render('/view/blocks/compare.mako.html')

def cat_breadcrumbs(current_cat={}):
    breadcrumbs = ''
    if current_cat:
        url = current_cat['URL']
        url = url[1:len(url)]
        categories = CategoriesModel
        splited = url.split('/')
        url = ''
        for item in splited:
            if item is '':
                continue
            url += '/' + item
            category = categories.getByURL(url)
            if category:
                breadcrumbs += '<li style="display: inline;"><a href="' + url + '/">'+ unicode(category["Name"]) + '</a></li>'
    else:
        breadcrumbs = u'<li style="display: inline;"><span>Главная</span></li>'
    c.breadcrumbs = HTML.literal(breadcrumbs)
    return render('/view/blocks/breadcrumbs.mako.html')

def market_breadcrumbs(market, cat):
    market_b = '<li style="display: inline;"><a href="/market/'+market['transformedTitle']+'/">'+market['title']+'</a></li>'
    cat_b = ''
    if cat:
        if cat.has_key('Name'):
            cat_b = '<li styel="display: inline;"><a href="/market/'+market['transformedTitle']+cat['URL']+'/">'+cat['Name']+'</a></li>' 
    breadcrumbs = market_b+cat_b
    c.breadcrumbs = HTML.literal(breadcrumbs)
    return render('/view/blocks/breadcrumbs.mako.html')
    

def vendor_breadcrumbs(vendor, cat):
    """
    возврацает хлебные крошки для страницы производителя
    Входные параметры:
        vendor = {} (dict) - текущий производитель
        cat = {} (dict) - текущая категория
    Параметры шаблонизатора:
        c.breadcrumbs = * (string) - сформированные хлебные крошки
    """
    vendor_b = '<li style="display: inline;"><a href="/vendor/'+vendor['transformedTitle']+'/">'+vendor['name']+'</a></li>'
    cat_b = ''
    if cat:
        if cat.has_key('Name'):
            cat_b = '<li styel="display: inline;"><a href="/vendor/'+vendor['transformedTitle']+cat['URL']+'/">'+cat['Name']+'</a></li>' 
    breadcrumbs = vendor_b+cat_b
    c.breadcrumbs = HTML.literal(breadcrumbs)
    return render('/view/blocks/breadcrumbs.mako.html')
    

def search_breadcrumbs(query, cat):
    """
    возврацает хлебные крошки для страницы производителя
    Входные параметры:
        vendor = {} (dict) - текущий производитель
        cat = {} (dict) - текущая категория
    Параметры шаблонизатора:
        c.breadcrumbs = * (string) - сформированные хлебные крошки
    """
    breadcrumbs = '<li style="display: inline;"><a href="/search/' + query + u'">Результаты поиска</a></li>'
    if cat:
        if cat.has_key('Name'):
            breadcrumbs += '<li style="display: inline;"><a href="/search/' + cat['URL']+query+'">' + cat['Name'] + '</a></li>' 
    c.breadcrumbs = HTML.literal(breadcrumbs)
    return render('/view/blocks/breadcrumbs.mako.html')


def static_pages_breadcrumbs(page_id):
    #TODO переделать на ясную голову

    static_pages_model = StaticPagesModel

    current_node = static_pages_model.get_by_id(page_id)
    def get_breadcrumbs(current_node):
        #TODO неясная проверка на наличие parent_id, заменить на id тоже не фонтан. Может смотреть на None с монги???
        if not current_node.has_key('parent_id'):
            return '<li class="home"><a href="%(url)s">%(title)s</a></li>' % \
                    {'title': current_node['title'],
                     'url'  : url('main_page') 
                    }

        parent_node = static_pages_model.get_by_id(current_node['parent_id'])
        return  get_breadcrumbs(parent_node) + \
                '<li><a href="%(url)s">%(title)s</a></li>' % \
                    {'title': current_node['title'],
                     'url'  : url('static_pages', static_page_slug=current_node['slug']) 
                    }
     
    c.breadcrumbs = h.literal(get_breadcrumbs(current_node)) 
    return render('/view/blocks/navigation/breadcrumbs/static_pages.mako.html')


def market_cats(market):
    if len(market)>0:
        reference_model = ReferenceModel
        categories_model = CategoriesModel
        tempo = reference_model.group(keys={'categoryId':True}, condition={'shopId': market['id']})
        cats = []
        for item in tempo:
            cats.append(item['categoryId'])

        cats = categories_model.get_by_ids(cats)

        c.cats = ''
        for cat in cats:
            if cat['ID'] != 0:
                c.cats += '<li class="show_tip"><a class="clickable" href="/market/' + market['transformedTitle'] + cat['URL'] + '/">' + cat['Name']+'</a><div class="proposal"><a href="' + cat['URL'] + u'/"><div title="Показать все товары этой категории на рынке" class="dotted-text">' +u'на рынок'+ '</div></a></div></li>'
        c.cats = HTML.literal(c.cats)
        return render('/view/blocks/market/cats.mako.html')
    else:
        return ""

def vendor_cats(vendor):
    if len(vendor):
        reference_model = ReferenceModel
        categories_model = CategoriesModel
        tempo = reference_model.group(keys={'categoryId':True}, condition={'vendor': vendor['id']})
        cats = []
        for item in tempo:
            cats.append(item['categoryId'])

        cats = categories_model.get_by_ids(cats)

        c.cats = ''
        for cat in cats:
            if cat['ID'] != 0:
                c.cats += '<li class="show_tip"><a class="clickable" href="/vendor/' + vendor['transformedTitle'] + cat['URL'] + '/">' + cat['Name']+'</a><div class="proposal"><a href="' + cat['URL'] + '/"><div class="dotted-text">' +u'на рынок'+ '</div></a></div></li>'
        c.cats = HTML.literal(c.cats)
        return render('/view/blocks/vendor/cats.mako.html')
    else:
        return ""

def search_cats(query, ids):    
    """Категории найденных товаров"""    
    if (query and ids) is None:
        return ""

    categories_model = CategoriesModel
    cats = categories_model.get_by_ids(ids)
    c.cats = ''
    for cat in cats:
        if cat['ID'] != 0:
            c.cats += '<li class="show_tip"><a class="clickable" href="/search' + cat['URL'] +query+ '">' + cat['Name']+'</a><div class="proposal"><a href="' + cat['URL'] + '/"><div class="dotted-text">' +u'на рынок'+ '</div></a></div></li>'
    c.cats = HTML.literal(c.cats)
    return render('/view/blocks/market/cats.mako.html')

def wishlist():
    if SettingsModel.wishlist_enabled():
        cookies = request.cookies.get('wishlist')
        if cookies:
            cookies = urllib.unquote(cookies).split(';;')
        else:
            cookies = []
        c.products = []
        tempo = []
        for cookie in cookies:
            if cookie != '':
                cookie = cookie.split('::')
                if cookie[0] not in tempo:
                    c.products.append(cookie)
                    tempo.append(cookie[0])
        
        return render('/view/blocks/wishlist.mako.html')
    else:
        return ""


#TODO переписать нафиг !!!!
def sort_panel(current_settings, current_url, price_min, price_max):
    if not isinstance(current_settings, dict):
        raise TypeError('current_setting must be dictionary')

    if not (len(current_settings) == 1 and (current_settings.has_key('price') or current_settings.has_key('popular') or current_settings.has_key('rating'))):
        raise Exception('current_settings must have one of this keys: {price, popular, rating}')

    c.key = current_settings.keys()[0]
    c.order = current_settings[c.key]
    sign = '?'
    if current_url.count('?'):
        sign = '&'
    current_url =  current_url[0:len(current_url) - 1]+'1'
    filters = '&price_min='+str(price_min)+'&price_max='+str(price_max)

    additional_params = ''
    raw_params = request.params
    tempo = ['price_min', 'price_max', 'sort_by', 'sort_order']
    for pr in raw_params:
        if pr not in tempo:
            additional_params += '&'+pr+'='+urllib.unquote(raw_params[pr])


    c.price_url = current_url+sign+'sort_by=price&sort_order=desc'+filters+additional_params
    c.popular_url = current_url+sign+'sort_by=popular&sort_order=desc'+filters+additional_params
    c.rating_url = current_url+sign+'sort_by=rating&sort_order=desc'+filters+additional_params

    if c.key == 'price':
        if c.order == 'asc':
                c.price_url = current_url+sign+'sort_by=price&sort_order=desc'+filters+additional_params
        else:
            c.price_url = current_url+sign+'sort_by=price&sort_order=asc'+filters+additional_params

    if c.key == 'popular':
        if c.order == 'asc':
            c.popular_url = current_url+sign+'sort_by=popular&sort_order=desc'+filters+additional_params
        else:
            c.popular_url = current_url+sign+'sort_by=popular&sort_order=asc'+filters+additional_params

    if c.key == 'rating':
        if c.order == 'asc':
            c.rating_url = current_url+sign+'sort_by=rating&sort_order=desc'+filters+additional_params
        else:
            c.rating_url = current_url+sign+'sort_by=rating&sort_order=asc'+filters+additional_params

    return render('/view/blocks/sort_panel.mako.html')


def product_preview(product, currency):
    """
    Генерация блока продукта
    Входные параметры product -     
    """
    c.is_wishlist = SettingsModel.wishlist_enabled()
    c.name = h.literal(product['title'].replace('"', '&#34;').replace('\'', '&#34;').replace('_',' '))
    if product[currency] > 0:
        
        price = math.modf(round(product[currency], 2))
        
        suffix = str(price[0])[2:4]
        if len(suffix)<2:
            suffix += '0'

        c.price = '%s<span class="price-suffix"><b>.</b>%s</span>' % (str(int(price[1])), suffix)
        
        if currency == 'UAH':
            c.price += u' грн'
        elif currency == 'USD':
            c.price = u'&#36;%s' % c.price
        elif currency == 'EUR':
            c.price = u'&euro;%s' % c.price
        elif currency == 'RUB':
            c.price += u' руб.'
    else:
        c.price = ''

    c.description = u'Описание отсутствует'
 
    if product.description and product.description.lower().find('none')<0:
        c.description = unicode(product['description'])
    c.image = thumb_image(product)
    c.url = make_product_url(product)    
    c.product_id = product['id']
    if not product.Rate:
        c.rating = 0
    else:
        c.rating = product['Rate']
    try: 
        int(c.product_id)
    except ValueError:
        raise Exception('product_id should be integer, <b>AND NOT OTHERWISE!!!</b>')
    return render('/view/blocks/product/preview.mako.html')


def make_product_url(product):    
    url = {}
    url['ip'] = request.environ['REMOTE_ADDR']
    url['url'] = product['url']
    url['dt'] = datetime.now()
    url['title'] = product['title']
    url['offerId'] = product['id']
    url['shopId'] = product['shopId']
    url['categoryId'] = product['categoryId']
    url['vendor'] = product['vendor']
    url['campaign_id'] = product['campaign_id']
    return "/redirect/redirect?url="+h.encode(url)   

def product_features():
    return render('/view/blocks/product/features.mako.html')

def product_prices():
    return render('/view/blocks/product/prices.mako.html')

def product_foto_video():
    return render('/view/blocks/product/foto_video.mako.html')

def product_likes():
    return render('/view/blocks/product/likes.mako.html')

def product_accessories():
    return render('/view/blocks/product/accessories.mako.html')

def product_price_dynamics():
    return render('/view/blocks/product/price-dynamics.mako.html')

def market_filters(category, vendors, market, currency, query):
    if not category:
        tempo_vendors = h.get_vendors_by_market(market['id'])
    else:
        tempo_vendors = h.get_vendors_by_category_and_market(category['ID'], market['id'])

    c.pop_markets = None
    c.markets = None
    c.market = market
    c.pop_vendors = []
    c.vendor = []
    c.vendors = []
    c.checked_vendors=[]
    c.currency = currency
    c.price_params = json.dumps(query)
    c.search_query = None
    c.cats = None

    counter = 0
    for vendor in tempo_vendors:
        if not vendor.has_key("transformedTitle"):
            pass
        if vendor is None or vendor['id'] == 100000:
            continue

        if vendor.has_key('popularity') and vendor['popularity'] > 0 and counter < 20:
            c.pop_vendors.append(vendor)
            counter += 1
        else:
            c.vendors.append(vendor)

    c.pop_vendors = bubble_sort_dict(c.pop_vendors, 'popularity')
    c.checked_vendors = vendors
    return render('/view/blocks/filters.mako.html')


def vendor_filters(price_min, price_max, affordable_price, category, markets, vendor, currency, query):
    """
    Рендерит фильтры для страницы производителя
    Входные параметры:
        price_min = (int) - минимальная цена (для установки фильтра по цене при загрузке страницы)
        price_max = (int) - максимальная цена (для установки фильтра по цене при загрузке страницы)
        affordable_price  = (int) - предельная цена (для установки фильтра по цене при загрузке страницы)
        category = {} (dict) - текущая категория данного производителя
        markets = [(int)] (list) - отмеченные магазины
        vendor = {} (dict) - текущий производитель
    Параметры шаблонизатора:
        c.markets = [(dict)] (list) - магазины без популярных
        c.pop_markets = [(dict)] (list) - популярные магазины
        c.checked_markets  = [(int)] (list) - id магазинов отмеченных в фильтре
        c.vendors  = None - фильтр по производителю не выводим
        c.pop_vendors = None - фильтр по производителю не выводим
    """
    tempo_markets= []
    if not category:
        tempo_markets = h.get_markets_by_vendor(vendor['id'])
    else:
        tempo_markets = h.get_markets_by_category_and_vendor(category['ID'], vendor['id'])

    c.pop_vendors = None 
    c.vendors = None
    c.pop_markets = []
    c.market = []
    c.markets = []
    c.checked_markets = []
    c.price_params = json.dumps(query)
    c.currency = currency
    c.search_query = None
    c.cats = None

    counter = 0
    for market in tempo_markets:
        if market['id'] == 100000:
            continue

        if market.has_key('popularity') and market['popularity'] > 0 and counter < 20:
            c.pop_markets.append(market)
            counter += 1
        else:
            c.markets.append(market)

    c.pop_markets = bubble_sort_dict(c.pop_markets, 'popularity')
    c.checked_markets = markets
    c.vendor = vendor

    return render('/view/blocks/filters.mako.html')

def search_filters(markets, checked_markets, vendors, checked_vendors, currency, price_query, search_query, cats):
    """
    Рендерит фильтры для страницы производителя
    Входные параметры:
        price_min = (int) - минимальная цена (для установки фильтра по цене при загрузке страницы)
        price_max = (int) - максимальная цена (для установки фильтра по цене при загрузке страницы)
        affordable_price  = (int) - предельная цена (для установки фильтра по цене при загрузке страницы)
        category = {} (dict) - текущая категория данного производителя
        markets = [(int)] (list) - отмеченные магазины
        vendor = {} (dict) - текущий производитель
    Параметры шаблонизатора:
        c.markets = [(dict)] (list) - магазины без популярных
        c.pop_markets = [(dict)] (list) - популярные магазины
        c.checked_markets  = [(int)] (list) - id магазинов отмеченных в фильтре
        c.vendors  = None - фильтр по производителю не выводим
        c.pop_vendors = None - фильтр по производителю не выводим
    """

    tempo_markets = MarketsModel.get_by_ids(markets)
    tempo_vendors = VendorsModel.get_by_ids(vendors)

    c.pop_vendors = [] 
    c.vendors = []
    c.vendor = []
    c.pop_markets = []
    c.markets = []
    c.market = []
    c.checked_markets = []
    c.price_params = json.dumps(price_query)
    c.currency = currency
    c.search_query = search_query
    c.cats = cats

    counter = 0
    for market in tempo_markets:
        if market['id'] == 100000:
            continue

        if market.has_key('popularity') and market['popularity'] > 0 and counter < 20:
            c.pop_markets.append(market)
            counter += 1
        else:
            c.markets.append(market)

    c.pop_markets = bubble_sort_dict(c.pop_markets, 'popularity')
    c.checked_markets = checked_markets

    counter = 0
    for vendor in tempo_vendors:
        if not vendor.has_key("transformedTitle"):
            continue

        if vendor is None or vendor['id'] == 100000:
            continue

        if vendor.has_key('popularity') and vendor['popularity'] > 0 and counter < 20:
            c.pop_vendors.append(vendor)
            counter += 1
        else:
            c.vendors.append(vendor)

    c.pop_vendors = bubble_sort_dict(c.pop_vendors, 'popularity')
    c.checked_vendors = checked_vendors

    return render('/view/blocks/filters.mako.html')

def category_filters(price_min, price_max, affordable_price, category_id, markets, vendors, currency):
    c.market = markets
    c.vendor = vendors
    c.price_max = price_max
    c.price_min = price_min
    c.affordable_price = int(affordable_price) 
    tempo_markets = h.get_markets_by_category(category_id)
    tempo_vendors = h.get_vendors_by_category(category_id)
    c.pop_vendors = []
    c.pop_markets = []
    c.vendors = []
    c.markets = []
    c.currency = currency
    c.price_params = json.dumps({'categoryId': category_id})
    c.search_query = None
    c.cats = None
    c.market = []
    c.vendor = []

    counter = 0
    for vendor in tempo_vendors:
        if vendor['id'] == 100000:
            continue

        if vendor.has_key('popularity') and vendor['popularity'] > 0 and counter < 20:
            c.pop_vendors.append(vendor)
            counter += 1
        else:
            c.vendors.append(vendor)

    for market in tempo_markets:
        if market.has_key('popularity') and market['popularity'] > 0:
            c.pop_markets.append(market)
        else:
            c.markets.append(market)

    c.pop_vendors = bubble_sort_dict(c.pop_vendors, 'popularity')
    c.pop_markets = bubble_sort_dict(c.pop_markets, 'popularity')


    c.checked_markets = markets
    c.checked_vendors = vendors
    return render('/view/blocks/filters.mako.html')

def bubble_sort_dict(tempo_dict, sort_key):

    flag = True
    while flag:
        flag = False
        for key in range(0, len(tempo_dict) - 1):
            if tempo_dict[key][sort_key] < tempo_dict[key + 1][sort_key]:
                temp = tempo_dict[key]
                tempo_dict[key] = tempo_dict[key + 1]
                tempo_dict[key + 1] = temp
                flag = True

    return tempo_dict

def paging_toolbar(current_page, total_pages):
    current_page = int(current_page)
    total_pages = int(total_pages)

    if total_pages == 1:
        return ''

    pager = ''
    
    if current_page <= 5 and total_pages >= 10:
        for x in range(1, 11):
            if current_page == x:
                pager += '<li>'+str(x)+'</li>'
            else:
                pager += '<li><a href="'+str(x)+'?'+request.query_string+'">'+str(x)+'</a></li>'

    elif current_page > (total_pages - 5) and total_pages >= 10:
        for x in range(total_pages - 8, total_pages+1):
            if current_page == x:
                pager += '<li>'+str(x)+'</li>'
            else:
                pager += '<li><a href="'+str(x)+'?'+request.query_string+'">'+str(x)+'</a></li>'
            
    elif current_page < 10 and total_pages < 10:
        for x in range(1, total_pages+1):
            if current_page == x:
                pager += '<li>'+str(x)+'</li>'
            else:
                pager += '<li><a href="'+str(x)+'?'+request.query_string+'">'+str(x)+'</a></li>'
    
    elif current_page > 5 and total_pages > 10:
        for x in range(current_page - 4, current_page + 5):
            if current_page == x:
                pager += '<li>'+str(x)+'</li>'
            else:
                pager += '<li><a href="'+str(x)+'?'+request.query_string+'">'+str(x)+'</a></li>'


    if current_page > 1:
        pager = '<div id="pager-center" align="center"><ul class="pager"><li class="to-start"><a href="1?'+request.query_string+'">to-start</a></li><li class="back"><a href="'+str(current_page-1)+'?'+request.query_string+'">back</a></li>'+pager
    else:
        pager = '<div id="pager-center" align="center"><ul class="pager">'+pager

    if current_page < total_pages:
        pager += '<li class="next"><a href="'+str(current_page + 1)+'?'+request.query_string+'">next</a></li><li class="to-end"><a href="'+str(total_pages)+'?'+request.query_string+'">to-end</a></li></ul></div>'
    else:
        pager += '</ul></div>'

    return HTML.literal(pager)

def footer_block():
    settings_model = SettingsModel
    c.footer_settings = settings_model.get_footer_settings()
    return render('/base/footer.mako.html')


def static_pages_navigation_menu(page_id):
    c.tree = h.get_navigation_tree(navigation_model=StaticPagesModel)(root_item_id=0, deep=5)
    c.page_id = page_id
    return render('/view/blocks/navigation/static_pages.mako.html')
