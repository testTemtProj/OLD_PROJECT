# coding: utf-8
import logging
import json
import xmlrpclib

from pylons import request, response, tmpl_context as c, url
from pylons import session
from pylons.controllers.util import abort, redirect

from manager.lib.base import BaseController, render
from manager.model.categoriesModel import CategoriesModel
from manager.model.marketsModel import MarketsModel
from manager.lib import helpers as h
from manager.lib.category_as_array import *

from pylons import config

log = logging.getLogger(__name__)

session['_cat'] = []
session['_shopId'] = None
session.save()

class CategoryController(BaseController):
    _cam = []
    
    def __init__(self):
        self.categoriesModel = CategoriesModel
        self.categories = None
        
        self.all_categories = self.categoriesModel.get_all()
        
        ADLOAD_XMLRPC_HOST = config.get('adload_xmlrpc_server')
        self.adload = xmlrpclib.ServerProxy(ADLOAD_XMLRPC_HOST)

    def clear_all(self):
        market_model = MarketsModel()
        market_model.clear_all()
        return 'Все магазины удалены с рынка'

    def getYottosTreeSettings(self):
        categories = get_childrens(self.all_categories ,int(request.POST.get('node')))
        tree = []
        for category in categories:
            if category['ID'] != category['ParentID']:
                tmp = {}
                tmp['id'] = category['ID']
                tmp['text'] = category['Name']
                tmp['cls'] = 'folder'
                tmp['draggable'] = True
                tmp['leaf'] = False
                tmp['editable'] = False
                tree.append(tmp)
        return json.dumps(tree)
    
    def getYottosTreeMatching(self):
        categories_model = CategoriesModel
        pattern = request.POST.get('pattern', False)
        node_id = request.POST.get('node', 0)

        try:
            node_id = int(node_id)
        except:
            node_id = 0
            
        categories = get_childrens(self.all_categories, node_id)
        tree = []
        
        if pattern:
            pattern = pattern.replace(' ', '|')
            import re
            search = re.compile('(%s)'%pattern, re.UNICODE | re.IGNORECASE)

        for category in categories:
            item = {}
            item['id'] = category['ID']
            item['text'] = category['Name']
            item['cls'] = 'folder'
            item['draggable'] = False
            item['editable'] = False
            item['has_children'] = categories_model.has_children(category['ID'])

            if not pattern or search.search(category['Name']) or self.is_in_child(category['ID'], pattern, search):
                tree.append(item)

        return json.dumps(tree)

    def is_in_child(self, category_id, pattern, search):
        if search:
            children_categories = get_childrens(self.all_categories, category_id)
            result = False
            for category in children_categories:
                result = search.search(category['Name']) or self.is_in_child(category['ID'], pattern, search)
                if result:
                    break
        else:
            result = False
            
        return result

    def get_parent_expand(self, id):
        category = find_category_in_array(self.all_categories, id)
        try:
            if category['ParentID'] != 0:
                if category['ID'] not in self._cam:
                    self._cam.append(category['ID'])
                self.get_parent_expand(category['ParentID'])
            else:
                if category['ID'] not in self._cam:
                    self._cam.append(category['ID'])
        except:
            pass
            
        return self._cam
    
    def get_node_to_expand(self):
        self._cam = []
        market_model = MarketsModel()
        cam = []
        comp = market_model.get_comparison(session['_shopId'])
        for x in comp:
            add = self.get_parent_expand(int(x['y_cat_id']))
            cam += add
        return cam

    def update_category_from_market(self):
        market_model = MarketsModel()
        updated_categories = []
        market_id = int(request.POST.get('market_id'))
        
        try:
            categories = self.adload.get_category_market_by_id(session['_shopId'])
        except Exception as message:
            result = {'success':False}
            return h.JSON(result)

        for category in categories:
            comparisons = market_model.get_comparison(market_id)
            category['id'] = int(category['id'])
            exists = False
            for comparison in comparisons:
                if category['id'] == comparison['shop_cat_id']:
                    exists = True
            if not exists:
                updated_categories.append(category)

        market_model.set_category(market_id, updated_categories)

        session['_shopId'] = market_id
        session['_cat'] = updated_categories
        session.save()

        result = {'success':True}
        
        return h.JSON(result)

    def get_category_from_market(self):
        market_model = MarketsModel()
        categories = {}
        session['_shopId'] = int(request.POST.get('market_id'))
        market = market_model.get_by_id(session['_shopId'])

        session['_cat'] = []
        
        if market and 'Categories' in market:
            session['_cat'] = market['Categories']

        session.save()
        self.set_parent_category()
        categories['expand'] = self.get_node_to_expand()
        
        comparisons = market_model.get_comparison(session['_shopId'])
            
        result = []
        for comparison in comparisons:
            if 'obg' in comparison:
                result.append(comparison['obg'])
                
        tmp = []
        to_del = []
        for id in result:
            index = result.index(id)
            if index not in tmp:
                tmp.append(index)
            else:
                to_del.append(id)
                
        for id in to_del:
            result.remove(id)
        
        categories['nodes'] = result
        return h.JSON(categories)
    
    def set_parent_category(self):
        for category in session['_cat']:
            if not 'parentId' in category:
                category['parentId'] = 0
        return

    def reparent(self):
        node_id = int(request.POST.get('node'))
        parent_id = int(request.POST.get('parent'))
        category = self.categoriesModel
        result = category.reparent(node_id = node_id, parent_id = parent_id)

        return h.JSON(result)

    def get_children_from_market(self, id):
        result = []

        for category in session['_cat']:
            if int(category['parentId']) == int(id):
                result.append(category)

        if int(id)==0 and len(result)==0 and len(session['_cat'])>0:
            raise BaseException('no_parents')
        else:
            return result
    
    def del_category_from_market(self, shop_id, cat_id):
        market_model = MarketsModel()
        cat = []
        
        try:
            categories = market_model.get_by_id(shop_id)['Categories']
        except:
            categories = self.adload.get_category_market_by_id(shop_id)
            market_model.set_category(shop_id, categories)
        
        for category in categories:
            if int(category['id']) != int(cat_id):
                cat.append(category)
        
        market_model.set_category(shop_id,cat)
        return

    def getShopTreeStatus(self):
        market_model = MarketsModel()
        try:
            self.get_children_from_market(0)
            comparisons = market_model.get_comparison(session['_shopId'])
            if comparisons:
                result = {'status':'in_comparison'}
            else:
                result = {'status':'no_categories'}

        except BaseException as message:
            result = {'status':'%s'%message}

        return json.dumps(result)

    def getShopTree(self):
        is_filter = True if request.POST.get('filter', False)=='true' else False
        pattern = request.POST.get('pattern', False)
        node_id = request.POST.get('node', 0)

        if is_filter and pattern:
            pattern = pattern.replace(' ', '|')
            import re
            search = re.compile('(%s)'%pattern, re.UNICODE | re.IGNORECASE)

        tree = []
        try:
            categories = self.get_children_from_market(node_id)
            for category in categories:
                current = {}
                is_leaf = len(self.get_children_from_market(category['id'])) < 1
                current['id'] = category['id']
                current['text'] = category['name']
                current['cls'] = 'folder'
                current['draggable'] = is_leaf
                current['leaf'] = is_leaf
                current['expanded'] = True
                
                if is_filter and pattern:
                    if search.search(category['name']) or (not is_leaf and self.is_in_child_tree(node_id, pattern, search)):
                        tree.append(current)
                else:
                    tree.append(current)

        except BaseException as message:
            tree = []

        return json.dumps(tree)

    def is_in_child_tree(self, category_id, pattern, search):
        if search:
            children_categories = self.get_children_from_market(category_id)
            result = False
            for category in children_categories:
                result = search.search(category['name']) or self.is_in_child_tree(category['id'], pattern, search)
                if result:
                    break
        else:
            result = False

        return result

    def get_category(self):
        return h.JSON(find_category_in_array(self.all_categories, int(request.POST.get('id'))))
    
    def remove(self):
        id = int(request.params.get('catId', -1))
        cat = self.categoriesModel
        res = cat.remove(id=id)

        return h.JSON(res)
    
    def rename(self):
        id = int(request.params.get('catId', -1))
        newName = request.params.get('newName', -1)
        cat = self.categoriesModel
        res = cat.rename(id=id, newName = newName)

        return h.JSON(res)
    
    def change(self):
        param = request.params.get('cat', None)
        param = json.loads(param)
        res = self.categoriesModel.change(param)

        return h.JSON(res)
    
    seo_str = ""

    def get_seo_str(self, parent_id):
        if parent_id == 0:
            return self.seo_str
        else:
            tmp = find_category_in_array(self.all_categories, parent_id)
            self.seo_str += tmp['Name'] + ", "
            self.get_seo_str(tmp['ParentID'])

        return self.seo_str

    def add(self):
        param = request.params.get('cat', None)
        param = json.loads(param)
        parent_id = int(param['ParentID'])
        if param['Description'] == '':
            param['Description'] = config.get('default_seo_description')
        if param['Title'] == '':
            param['Title'] = config.get('default_title_f_part').decode('UTF-8') + " " + param['Name']
        if param['MetaKey'] == '':
            if parent_id > 0:
                self.get_seo_str(parent_id)
            self.seo_str = self.seo_str[0:len(self.seo_str)-2]
            param['MetaKey'] = self.seo_str

        if parent_id > 0:
            parent_category = find_category_in_array(self.all_categories, parent_id)
            param['URL'] = parent_category['URL']+'/'+h.translate(param['Name'])
        else:
            param['URL'] = '/'+h.translate(param['Name'])

        param['count'] = 0    
        saved_params = self.categoriesModel.save(param)
        return json.dumps(saved_params)

    def get_Markets(self):
        market_model = MarketsModel()
        limit = request.params.get('limit', 20)
        start = request.params.get('start', 0)
        markets = market_model.get_all(start, limit)
        m = []
        total = market_model.get_count()

        for x in markets:
            tmp = {}
            tmp['title'] = x['title']
            tmp['id'] = x['id']
            tmp['urlMarket'] = x['urlMarket']
            m.append(tmp)

        result = {"total": str(total), "data": m}

        return json.dumps(result)

    comparison = []
    
    def set_children_for_comparison(self, add_to, cat_id, comp):
        children = self.get_children_from_market(cat_id)

        for x in children:
            tmp = {}
            tmp['y_cat_id'] = add_to
            tmp['shop_cat_id'] = x['id']
            x['pId'] = add_to
            tmp['obg'] = x
            self.comparison.append(tmp)
            
            self.del_category_from_market(session['_shopId'], x['id'])
            if len(self.get_children_from_market(x['id'])) != 0:
                self.set_children_for_comparison(add_to, x['id'],comp)
            
        return self.comparison
        
    def re_compare(self):
        market_model = MarketsModel()
        add_to = int(request.POST.get('target'))
        old = int(request.POST.get('old'))
        cur_node = int(request.POST.get('cur_node'))
        cur_market_cat = None

        comp = market_model.get_comparison(session['_shopId'])
        
        name = ''

        for comparison in comp:
            if int(comparison['shop_cat_id']) == cur_node:
                cur_market_cat = comparison['obg']
                name = comparison['obg']['name']
                comp.remove(comparison)
                break

        if add_to > 0:
            cur_comp = {'y_cat_id': add_to, 'shop_cat_id': cur_node, 'obg': cur_market_cat}
            self.del_category_from_market(session['_shopId'], cur_node)
            comp.append(cur_comp)
        else:
            categories = market_model.get_by_id(session['_shopId'])['Categories']
            category = {
                "name": name,
                "id": cur_node
            }
            categories.append(category)
            market_model.set_category(session['_shopId'], categories)
        
        market_model.set_comporison(int(session['_shopId']), comp)
        session.save()

    def reset_comparisons(self):
        market_id = int(request.POST.get('market_id'))

        market_model = MarketsModel()
        
        comparisons = market_model.get_comparison(market_id)
        categories  = market_model.get_by_id(market_id)['Categories']
        for comparison in comparisons:
            if comparison['obg']:
                category = {
#                    'parentId': comparison['obg']['pId'],
                    'id': comparison['obg']['id'],
                    'name': comparison['obg']['name']
                }
                categories.append(category)

        market_model.set_category(market_id, categories)
        market_model.set_comporison(market_id, [])

        return 'ok'

    def add_comparison(self):
        market_model = MarketsModel()
        
        add_to = int(request.POST.get('target'))
        cur_node = int(request.POST.get('cur_node'))
        comp = market_model.get_comparison(session['_shopId'])

        try:
            market_categories = market_model.get_by_id(session['_shopId'])['Categories']
        except:
            market_categories = self.adload.get_category_market_by_id(session['_shopId'])
            market_model.set_category(session['_shopId'], market_categories)
        
        cur_market_cat = None
        
        for x in market_categories:
            if int(x['id']) == cur_node:
                x['pId'] = add_to
                cur_market_cat = x
                break
        
        cur_comp = {'y_cat_id': add_to, 'shop_cat_id': cur_node, 'obg': cur_market_cat}
        self.del_category_from_market(session['_shopId'], cur_node)
        comp.append(cur_comp)
        comp = comp + self.set_children_for_comparison(add_to, cur_node, comp)
        market_model.set_comporison(int(session['_shopId']), comp)
        session.save()

        return 'ok'
