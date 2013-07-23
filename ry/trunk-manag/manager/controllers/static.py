# coding: utf-8
import logging
import json

from webhelpers.html import HTML 
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from manager.lib.base import BaseController, render
from manager.model.staticPagesModel import StaticPagesModel

log = logging.getLogger(__name__)

class StaticController(BaseController):

    def __before__(self):
        #редиректим, если не ajax запрос
        if not request.is_xhr:
            return abort(status_code=404)


    def get_pages_tree(self):
        if request.params.get('node') == 'new-node':
            return []

        static_pages_model = StaticPagesModel

        node = int(request.POST.get('node'))

        pages = static_pages_model.get_children(node)

        tree = []
        for page in pages:
            tmp = {}
            tmp['id'] = page['id']
            tmp['text'] = page['title']
            tmp['cls'] = 'folder',
            tmp['draggable'] = False,
            if static_pages_model.get_children(page['id']).count() == 0:
                tmp['leaf'] = True
            else:
                tmp['leaf'] = False
            tree.append(tmp)
        return json.dumps(tree)


    def get_page(self):
        static_pages_model = StaticPagesModel

        page_id = int(request.POST.get('page_id'))

        page = static_pages_model.get_by_id(page_id)


        if page is None or not page.has_key('content'):
            return json.dumps({'success' : False, 'data' : {}});
        else:
            c.content = page['content']

        del page['_id']

        return json.dumps({'success' : True, 'data' : page})


    def save_page(self):
        static_pages_model = StaticPagesModel
        page_id = static_pages_model.save(request.params)
        
        return json.dumps({'page_id':page_id})

    
    def remove_page(self):
        static_pages_model = StaticPagesModel
        page_id = request.params.get('page_id', None)
        
        static_pages_model.remove(page_id)
