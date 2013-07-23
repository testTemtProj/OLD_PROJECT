import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rynok.lib.base import BaseController, render
from rynok.model.referenceModel import ReferenceModel

log = logging.getLogger(__name__)

class PopularProductsController(BaseController):

    def index(self):
        return render('/popular.products.mako.html')
