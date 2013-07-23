# coding: utf-8
import json
from rynok.lib.base import BaseController, render
from pylons import request, response, session, tmpl_context as c, url
from rynok.model.referenceModel import ReferenceModel
from pylons.controllers.util import abort, redirect
import rynok.lib.helpers as h

class ProductController(BaseController):
    def __init__(self):
        BaseController.__init__(self)
        self.reference_model = ReferenceModel

    def evaluate(self):
        if not request.is_xhr:
            return abort(status_code=404)

        score = float(request.params.get('score'))
        product_id = request.params.get('product_id')

        product = self.reference_model.get_by_id(product_id)

        if not product.Rate:
            product.Rate = score
            product.TotalRate = score
            product.RateCount = 1
            product.save()
            return json.dumps({'score': h.round_rating(score)})
        else:
            product.TotalRate +=score
            product.RateCount += 1
            product.Rate = h.round_rating(product.TotalRate / product.RateCount)
            product.save()
            return json.dumps({'score': product.Rate})

    def comments(self, id):
        c.product_id = id
        return render('/comments.product.mako.html')

    def get_filter_options(self):
        if not request.is_xhr:
            return abort(status_code=404)

        filter_type = request.params.get('filter_type')

        try:
            params = json.loads(request.params.get('params', '{}'))
        except ValueError:
            print "bad params in product.py get_filter_options() 47"
            params = {}

        if filter_type == 'price':
            if params.has_key('query') and params.has_key('currency'):
                query = params['query']
                currency = params['currency']
                affordable_price = self.reference_model.get_max_price(query, currency) + 1
                return json.dumps({'price_min': 0, 'price_max': int(affordable_price)})
            else:
                print "please check c.price_params in filter's view helper"
                return 'false'

        """
            Вставьте свои параметры для других фильтров
        """

        pass
