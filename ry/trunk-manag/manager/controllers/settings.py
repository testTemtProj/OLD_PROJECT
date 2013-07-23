# coding: utf-8
import logging
import json
import trans
import re

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from manager.lib.base import BaseController, render
from manager.model.categoriesModel import CategoriesModel
from manager.model.settingsModel import SettingsModel
from manager.model.staticPagesModel import StaticPagesModel

log = logging.getLogger(__name__)

class SettingsController(BaseController):

    def index(self):
        
        """
            Функция для отображения физуального интерфейса пользователя
        """
        
        if session.has_key('login'):
            return render('/login/login.mako.html')
        else:
            return render('/login/login.mako.html')
    
    def get_settings(self):
        
        """
            Функция для получения уже имеющихся настроек
            
            Возвращает:
                Ассоциативный массив настроек который состоит из:
                    cart - состояние корзины(True - показывать, 
                           False - не показывать)
                    count - количество выводимых товаров на странице
                    fields - ссылки для вывода в нижней части сайти
                    vishlist - состояние вишлиств(Ture - показывать, 
                               False - не показывать)
                    mainFields - список и порядок выводимых категорий на 
                                 главной странице
                    colsCatsNewGoods - количество категорий в блоке 
                                       "новые товары"
                    baner - код для вставки банера
                    colPopGoods - количество популярных товаров для каждой
                                  категории
                    colsNewGoods - количество новых товаров для каждой 
                                   категории
                    type - тип выводимых категорий(3х2 или 3х3)
                    colCatsPopGoods - количество категорий в блоке 
                                      "популярные товары"
                    searchBaner - банер для страницы поиска
        """
        
        CM = CategoriesModel
        static_pages_model = StaticPagesModel
        SM = SettingsModel
        cat = []
        result = {}
        
        for x in CM.get_by_parent_id(parentId=0, empty=False):
            cat.append(x['Name'])

        settings = SM.get_all()

        for x in settings:
            if x['name'] == 'common':
                result['cart'] = x['cart']
                result['count'] = x['count']
                result['fields'] = x['fields']
                result['vishlist'] = x['vishlist']

            if x['name'] == 'mainPage':
                result['mainFields'] = x['fields']
                result['colsCatsNewGoods'] = x['colsCatsNewGoods']
                result['baner'] = x['baner']
                result['colPopGoods'] = x['colPopGoods']
                result['colsNewGoods'] = x['colsNewGoods']
                result['type'] = x['type']
                result['colCatsPopGoods'] = x['colCatsPopGoods']

            if x['name'] == 'searchPage':
                result['searchBaner'] = x['baner']
        
        result['categories'] = cat
        
        return json.dumps(result)
    
    def save_common_settings(self):
        
        """
            Функция для сохранения общих настроек страниц
        """
        
        SM = SettingsModel
        static_pages_model = StaticPagesModel
        countLots = request.params.get('goodsCount')
        goods = False
        vishlist = False
        
        if request.params.get('goods') == 'on':
            goods = True
            
        if request.params.get('vishlist') == 'on':
            vishlist = True
            
        footer = []
        for x in range(0,20):
            text = request.params.get('lincText_'+str(x))
            link = request.params.get('linc_'+str(x))
            
            if not link:
                link = '#'
            
            html_link = "<a href='"+link+"'>"+text+"</a>"

            footer.append(html_link)
            
        result = {}
        result['name'] = 'common'
        result['count'] = countLots
        result['cart'] = goods
        result['vishlist'] = vishlist
        result['fields'] = footer
        
        SM.save_common_settings(result)
    
    def save_main_page_settings(self):
        
        """
            Функция для сохранения настроек для главной страницы
        """
        
        SM = SettingsModel
        type = request.params.get('type')
        colCatsPopGoods = request.params.get('colCatsPopGoods')
        colPopGoods = request.params.get('colPopGoods')
        colsCatsNewGoods = request.params.get('colsCatsNewGoods')
        colsNewGoods = request.params.get('colsNewGoods')
        baner = request.params.get('baner')
        fields = []
        if type == '3x2':
            for x in range(1,7):
                fields.append(request.params.get('2pos'+str(x)))
                
        elif type == '3x3':
            for x in range(1,10):
                fields.append(request.params.get('3pos'+str(x)))
                
        result = {}
        result['name'] = 'mainPage'
        result['type'] = type
        result['colCatsPopGoods'] = colCatsPopGoods
        result['colPopGoods'] = colPopGoods
        result['colsCatsNewGoods'] = colsCatsNewGoods
        result['colsNewGoods'] = colsNewGoods
        result['baner'] = baner
        result['fields'] = fields
        
        SM.save_common_settings(result)
    
    def save_search_settings(self):
        
        """
            Функция для сохранения настроек страницы поиска
        """
        
        SM = SettingsModel
        baner = request.params.get('baner')
        result = {}
        result['baner'] = baner
        result['name'] = 'searchPage'
        
        SM.save_common_settings(result)

    def edit_static_page(self):

        static_pages_model = StaticPagesModel
        page_translitedTitle = request.params.get('page', 'add_new_page')

        page = static_pages_model.get_by_translitedTitle(page_translitedTitle) 

        if page_translitedTitle == 'add_new_page' or page is None:
            c.title = ''
            c.content = ''
            c.translitedTitle = None
        else:
            c.title = page['title']
            c.content = page['content']
            c.translitedTitle = page['translitedTitle']

        return render('/settings/editStaticPage.mako.html')


    def save_static_page(self):
        static_pages_model = StaticPagesModel

        static_page_translitedTitle = request.params.get('translitedTitle', None)
        static_page_title = request.params.get('title', 'Не заполнено')
        static_page_content = request.params.get('content', '')

        new_page = {}

        if static_page_translitedTitle is not None:
            new_page = static_pages_model.get_by_translitedTitle(static_page_translitedTitle)
            if new_page is None:
                new_page = {}
            

        new_page['translitedTitle'] = re.compile(r'[^\w+]').sub('_', trans.trans(static_page_title)[0])

        new_page['title'] = static_page_title
        new_page['content'] = static_page_content

        static_pages_model.save(new_page)

        return redirect(url(controller='settings', action='edit_static_page', page=new_page['translitedTitle']))


    def get_static_pages_titles(self):
        static_pages_model = StaticPagesModel
        titles = static_pages_model.get_all_titles()

        titles.append(['add_new_page', u'добавить новую страницу...'])

        return json.dumps(titles)
