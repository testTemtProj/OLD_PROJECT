import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from manager.lib.base import BaseController, render

log = logging.getLogger(__name__)

class AuthController(BaseController):

    def private(self):
        if request.environ.get("REMOTE_USER"):
            return "You are authenticated as %s!" % request.environ.get("REMOTE_USER")
        else:
            response.status = "401 Not authenticated"
            return "You are not authenticated"

    def signout(self):
        return 'Successfully signed out!'
