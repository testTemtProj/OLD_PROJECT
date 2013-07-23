import logging

from webhelpers.html import HTML

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rynok.lib.base import BaseController, render
from rynok.model.staticPagesModel import StaticPagesModel

log = logging.getLogger(__name__)

class StaticController(BaseController):

    def view(self, static_page_slug):
        static_pages_model = StaticPagesModel
        page = static_pages_model.get_by_slug(static_page_slug)

        if page is None:
            abort(status_code=404)

        c.page_id = page['id']
        c.title = page['title']
        c.content = HTML.literal(page['content'])
        c.model = static_pages_model

        return render('/static.mako.html')
