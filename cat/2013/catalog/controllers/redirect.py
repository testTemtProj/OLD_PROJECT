import logging
import base64

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

import catalog.lib.helpers as h
from catalog.lib.base import BaseController, render
from catalog.model.CategoryModel import CategoryModel


log = logging.getLogger(__name__)

class RedirectController(BaseController):

    def redirect(self):
        url = request.params.get("url", None)
        if url:
            dest = base64.b64decode(url)
            return redirect(dest, 301)
        return redirect(url(controller="category", action="index"), 301)

