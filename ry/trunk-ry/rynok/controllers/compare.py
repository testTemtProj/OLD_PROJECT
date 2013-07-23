# coding: utf-8
from rynok.lib.base import BaseController, render
from webhelpers.html.builder import HTML
from pylons import request, response, session, tmpl_context as c, url
from rynok.model.productsModel import ProductsModel
from rynok.model.treeModel import TreeModel
from pylons.decorators.cache import *
import pymongo
from pylons.controllers.util import redirect
class CompareController(BaseController):
    def __init__(self):
        BaseController.__init__(self)
        self.tree_model = TreeModel()
        self.tree = self.tree_model.getTree()

    def index(self):
        id = request.params.get('id', False)
        return self._show(id)

    def _redirect(self, products):
        db = pymongo.Connection("rynok.yt:27020").stat
        db.Clicks.insert({'LotID':products['LotID'], 'ClickCost':products['ClickCost']})
        return redirect(products['URL'], 301)

    def _show(self, ids):
        product = ProductsModel()
        ids = [469167, 469166, 461668]
        compare_products = []
        products = product.getProduct(where={"LotID":{"$in":ids}})
        compare_products = products
        l = len(products)
        count = 1
        for p in products:
            for comp in compare_products:
                if comp==p:
                    print p['LotID']
        products = {}
        c.id=-1
        c.img = products.get('ImageURL', '')
        c.price = products.get('Price', '0')
        c.title = products.get('Title', '')
        c.descr = products.get('Descr', '')
        return render('/compare.mako.html')
        #else:
        #    return self._redirect(products)

    def show(self, product_title, product_id):
        id = product_id
        c.id = id
        return self._show(int(id))

    def click(self):
        id = request.params.get('LotID', -1)
        product = ProductsModel()
        products = product.getById(int(id))
        return self._redirect(products)

