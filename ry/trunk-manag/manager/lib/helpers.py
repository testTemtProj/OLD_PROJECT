# coding: utf-8
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from webhelpers.html.tags import *
from webhelpers.html.builder import HTML
import json
import pymongo.json_util
from trans import trans
from pylons import url
def JSON(obj):
    """Возвращает JSON-представление объекта obj"""
    return json.dumps(obj, default=pymongo.json_util.default, ensure_ascii=False)

def translate(s):
    """Возвращает транслетированую строку"""
    s = s.replace(" ","_")
    return trans(s)[0]

def build_paging(pages, current_page, url):
    """
    Строит пейджинг исходя из параметров
    """
    START = (current_page - (5 - abs(current_page - 5))) + 1 if current_page < 5 else current_page - 4
    END = START + 10 if (START + 10) < pages else pages
    res = ""
    if current_page > abs(START - 6):
        res += u"<a href='/%s'>Первая</a>&nbsp;" % (url)
    for page in xrange(START, END):
        if page == current_page + 1:
            res += u"<a href='/%s/%s' style='color:red;'>%s&nbsp;</a>" % (url, page, page)
        else:
            res += u"<a href='/%s/%s'>%s&nbsp;</a>" % (url, page, page)
    if pages - current_page > 6:
            res += u"&nbsp;<a href='/%s/%s'>Последняя</a>" % (url, pages - 1)
    return HTML.literal(res)

