import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import urllib
from rynok.lib.base import BaseController, render

log = logging.getLogger(__name__)

class SuggestController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/suggest.mako')
        # or, return a string
        #http://getmyad.vsrv-1.3.yottos.com/
        try:
#            URL = "http://getmyad.vsrv-1.3.yottos.com/suggest.fcgi?" + request.query_string
            URL = "http://suggest.yottos.com//testrynoksuggest.fcgi?" + request.query_string
            
            f = urllib.urlopen(URL)
            res = f.read()
#            print "%s\n%s"%(URL, res)
        except IOError, ex:
            print ex
            res = ""
        finally:
            f.close()
        return res
    
