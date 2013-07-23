# coding: utf-8
import logging

from pylons import request, response, session, tmpl_context as c, url,\
    app_globals
from pylons.controllers.util import abort, redirect


from getmyad.lib.base import BaseController, render
from getmyad.model import InformerFtpUploader

log = logging.getLogger(__name__)

class AdminController(BaseController):

    def update_reserve(self):
        ''' Перезаливка заглушек на FTP '''
        for i in app_globals.db.informer.find({}, ['guid']):
            InformerFtpUploader(i['guid']).upload_reserve()
