import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rynok.lib.base import BaseController, render
from rynok.model.referenceModel import ReferenceModel

log = logging.getLogger(__name__)

class NewProductsController(BaseController):

    def index(self):
        return render('/new.products.mako.html')
