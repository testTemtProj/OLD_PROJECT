# coding: utf-8
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rynok.lib.base import BaseController, render
from rynok.lib import helpers as h
from rynok.lib.tasks import process_click 
log = logging.getLogger(__name__)
from datetime import datetime 

class RedirectController(BaseController):


    def redirect(self):
        ''' Редирект на товар магазина
        Использует следующие GET параметры:
            ``url``      url назначения (куда редиректим) в base64.            
            ``id``       guid рекламного предложения
        '''

        purl = request.params.get("url", 'None')
        if purl is 'None':
            return redirect(url('main_page'), 301)

        params = h.decode(str(purl))
        if not params.has_key('ip'):
            params['ip'] = request.environ['REMOTE_ADDR']

        if not params.has_key('dt') or not isinstance(params['dt'], datetime):
            params['dt'] = datetime.now()

        #TODO логировать 
        try:
            task = process_click.delay(params)
        except Exception as ex:
            print ex
            process_click(params)

        if params.has_key('url'):
            redirect(params['url'], 301)
        else:
            redurect(url('main_page'))
