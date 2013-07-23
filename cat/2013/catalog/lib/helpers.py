#-*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
from webhelpers.html.tags import *
from webhelpers.html import *
from pylons import session, request
from pylons.i18n import get_lang, set_lang
from decorator import decorator
from bson import json_util
import re
import pymongo
import json
from datetime import date
import base64
from catalog.model.modelBase import Base

@decorator
def localize(f, *args, **kwargs):
    if 'lang' in session:
        set_lang(session['lang'])
    return f(*args, **kwargs)

def paging_toolbar(current_page, total_pages):
    current_page = int(current_page)
    total_pages = int(total_pages)
    current_url = re.sub(r'/(\d+)',r'',request.path_url)# if r'\1' == current_page else request.path_url

    if total_pages == 1:
        return ''

    pager = ''
    
    if current_page <= 5 and total_pages >= 10:
        for x in range(1, 11):
            if current_page == x:
                pager += str(x) + ""
            else:
                pager += '<a href="'+current_url+'/'+str(x)+'?'+request.query_string+'" class="pager">'+str(x)+'</a>'

    elif current_page > (total_pages - 5) and total_pages >= 10:
        for x in range(total_pages - 8, total_pages+1):
            if current_page == x:
                pager += str(x) + ""
            else:
                pager += '<a href="'+current_url+'/'+str(x)+'?'+request.query_string+'" class="pager">'+str(x)+'</a>'
            
    elif current_page < 10 and total_pages < 10:
        for x in range(1, total_pages+1):
            if current_page == x:
                pager += str(x) + ""
            else:
                pager += '<a href="'+current_url+'/'+str(x)+'?'+request.query_string+'" class="pager">'+str(x)+'</a>'
    
    elif current_page > 5 and total_pages > 10:
        for x in range(current_page - 4, current_page + 5):
            if current_page == x:
                pager += str(x) + ""
            else:
                pager += '<a href="'+current_url+'/'+str(x)+'?'+request.query_string+'" class="pager">'+str(x)+'</a>'


    if current_page > 1:
        pager = '<div id="pager-center" align="center"><a href="1?'+request.query_string+' class="pager"><img src="/Image/double-prev.gif" border=0></a><a href="'+str(current_page-1)+'?'+request.query_string+'" class="pager"><img src="/Image/prev.gif" border=0></a>'+pager
    else:
        pager = '<div id="pager-center" align="center">'+pager

    if current_page < total_pages:
        pager += '<a href="'+current_url+'/'+str(current_page + 1)+'?'+request.query_string+'"class="pager"><img src="/Image/next.gif" border=0></a><a href="'+current_url+'/'+str(total_pages)+'?'+request.query_string+'" class="pager"><img src="/Image/double-next.gif" border=0></a></div>'
    else:
        pager += '</div>'

    return HTML.literal(pager)



def get_tree(category={},lang='ru'):
    collection = Base.category_collection
    tree = {}
    
    if not category:
        parent_id = 0 
        tree = get_tree(collection.find_one({"id":0}),lang)

    else:
        if re.search(u'[a-zA-Zа-яА-я]+', category['title_'+lang]):
            category['title'] = category['title_'+lang]

        parent_id = int(category["id"])
        tree['data'] = category["title"] 
        tree['text'] = category["title"] 
        tree['id'] = category.get("id",0)
        tree['metadata']={'id':category["id"]} if category else {'id':0}
        tree['children'] = []

        if collection.find({'parent_id':parent_id}).count() > 0:
            for cat in collection.find({'parent_id':parent_id}):
                tree['children'].append(get_tree(cat,lang))
        else:
            del tree['children']
            tree['leaf'] = True
    return tree


def get_current_locale():
    if 'lang' in session:
        return session['lang']

def get_sites(category_id,start=0,limit=10):
    collection = Base.site_collection

    sites = {"sites":[], "total": collection.find({"category_id":int(category_id)}).count(), "success": True}
    
    for site in collection.find({"category_id":int(category_id)}).limit(limit).skip(start):
        del site['_id']
        site["date_add"] = re.search(r'\d{4}-\d{1,2}-\d{1,2}', str(site["date_add"])).group() #str(site["date_add"])
        site["last_checked"] = re.search(r'\d{4}-\d{1,2}-\d{1,2}', str(site.get("last_checked", site["date_add"]))).group()
        sites["sites"].append(site)
    return sites

def get_filtered_sites(filter, start=0, limit=10):
    collection = Base.site_collection

    sites = {'sites': [], 'total': collection.find({'$and':filter}).count(), 'success': True}

    for site in collection.find({'$and':filter}).limit(limit).skip(start):
        del site['_id']
        site["date_add"] = re.search(r'\d{4}-\d{1,2}-\d{1,2}', str(site["date_add"])).group() #str(site["date_add"])
        site["last_checked"] = re.search(r'\d{4}-\d{1,2}-\d{1,2}', str(site.get("last_checked", site["date_add"]))).group()
        sites["sites"].append(site)
    return sites


def get_leafs():
    collection = Base.category_collection
    leafs = collection.find({'is_leaf': 1},{'id':1, 'title':1})
    result = []
    for cat in leafs:
        del cat['_id']
        a_cat = [cat['id'],cat['title']]
        result.append(a_cat)
    return result
