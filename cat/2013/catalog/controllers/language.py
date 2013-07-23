import logging
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import catalog.lib.helpers as h
from catalog.lib.base import BaseController, render
from urlparse import urlparse
from pylons.i18n import get_lang, set_lang
from catalog.lib.base import *
from pylons import session
log = logging.getLogger(__name__)

class LanguageController(BaseController):

    def change(self):
        if 'lang' in request.GET and request.GET['lang'] in ['ru','en','uk']:
            session['lang'] = request.GET['lang']
            session.save()
        if 'HTTP_REFERER' in request.environ and not urlparse(request.environ['HTTP_REFERER']).netloc == request.environ['HTTP_HOST'] or not 'HTTP_REFERER' in request.environ:
            return redirect('/')
        return redirect(request.environ['HTTP_REFERER'])
