#-*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from pylons import session, request, response, url
from pylons.i18n import get_lang, set_lang
from pylons.i18n.translation import _, ungettext
from decorator import decorator
import json

def styleProjectName(name):
    plase_ad = name.lower().find('ad',len(name)-2,len(name))
    if plase_ad > 0 :
        result = '<span style="color:#4263dd;display:inline;margin:0;padding:0;">' +\
                name[0:plase_ad] +\
                '</span><span style="color:#f25204;display:inline;margin:0;padding:0;">ad</span>'
    else:
        result = name
    return result

@decorator
def localize(f, *args, **kwargs):
    if 'lang' in session:
        lang = session['lang']
        set_lang(lang)
    else:
        suport_lang = ['ru','en','uk']
        suport_domain = ['cleverad.yt:5000','10.0.0.8:5000']
        default_lang = 'ru'
        lang_cookie = request.cookies.get('lang', None)
        if not lang_cookie in suport_lang:
            lang_cookie = None
        domain = request.environ.get('HTTP_HOST', None)
        if not domain in suport_domain:
            domain = None
        if lang_cookie != None:
            lang = lang_cookie
        else:
            if domain == 'cleverad.yt:5000':
                lang = 'en'
            elif domain == '10.0.0.8:5000':
                lang = 'uk'
            elif domain == '10.0.0.8':
                lang = 'ru'
            else:
                lang = default_lang
        session['lang'] = lang
        session.save()
        set_lang(lang)
    response.set_cookie('lang', lang, max_age=360*24*3600 )
    return f(*args, **kwargs)
def rulesLink(link):
    rulesLink= []
    curentRulesTitle = _(u'Текущая версия')
    oldRulesTitle = _(u'Предыдущая версия')
    rulesLink.append("<div id='old-rules'>")
    curentUrl = url.current()
    if len(link) > 0:
        for item in link:
            urlLink = curentUrl +"/"+ item.strftime("%Y-%m-%d-%H-%M-%S")
            urlLink = '<a href="' + urlLink + '">' + oldRulesTitle + ' ' + item.strftime("%Y-%m-%d %H:%M:%S")  + '</a>'
            rulesLink.append("<span>")
            rulesLink.append(urlLink)
            rulesLink.append("</span>")
    else:
        urlLink = curentUrl[0:(curentUrl.lower().find('/rules') + 6)]
        urlLink = '<a href="' + urlLink + '">' + curentRulesTitle + '</a>'
        rulesLink.append("<span>")
        rulesLink.append(urlLink)
        rulesLink.append("</span>")
    rulesLink.append("</div>")
    rulesLink = " ".join(rulesLink)
    return rulesLink
def JSON(obj):
    """Возвращает JSON-представление объекта obj"""
    return json.dumps(obj, ensure_ascii=False)

def jgridDataWrapper(data, page=None, records_on_page=None, count=None, total_pages=None,
                     json=True):
    """ Принимает список значений колонок и возвращает json для таблиц jqGrid.
        Строит пейджинг по массиву данных или передает параметры пейджинга передаваемые
        ему на вход (при условии организации пейджинга с учётом выборки с бд)
        Для организации пейджинга из массива данных можно передать параметры ``page`` -- номер
        текущей страницы, ``records_on_page`` -- количество записей на одной
        странице.
        Для организации пейджинга при условии организации с учётом выборки с бд можно передать параметры
        ``page`` -- номер текущей страницы, ``count``- колво записей, ``total_pages`` - колво страниц.
    """
    if count is None and total_pages is None:
        records = len(data)
        if page is not None and records_on_page is not None:
            try:
                page = int(page)
            except ValueError:
                page = 1

            try:
                records_on_page = int(records_on_page)
            except ValueError:
                records_on_page = 20

            if page == 0:
                page = 1
            start_record = (page - 1) * records_on_page
            end_record = page * records_on_page
            total_pages = (records-1) / records_on_page + 1
            data = data[start_record:end_record]
            records = len(data)
        else:
            if records:
                total_pages = page = 1
            else:
                total_pages = page = 0
    else:
        records = int(count)
        try:
            total_pages = int(total_pages)
        except ValueError:
            total_pages = 1
        try:
            page = int(page)
        except ValueError:
            page = 1
        
    output = {'total': total_pages,
               'page': page,
               'records': records,
               'rows': [{'cell': x, 'id': index + 1}
                        for index,x in enumerate(data)]
               }
    return JSON(output) if json else output
def trim_by_words(str, max_len):
    ''' Обрезает строку ``str`` до длины не более ``max_len`` с учётом слов '''
    if len(str) <= max_len:
        return str
    trimmed_simple = str[:max_len]
    trimmed_by_words = trimmed_simple.rpartition(' ')[0]
    return u'%s…' % (trimmed_by_words or trimmed_simple)
