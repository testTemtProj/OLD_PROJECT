# encoding: utf-8
from getmyad.lib.base import BaseController, render
from getmyad.tasks import tasks
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import base64
import datetime
import logging


log = logging.getLogger(__name__)

class AdshowController(BaseController):

    def redirect(self):
        ''' Редирект на рекламное предложение.
        
        Использует следующие GET параметры:
            
            ``url`` -- url назначения (куда редиректим) в base64.
            ``inf`` -- guid информера, с которого производим редирект
            ``id`` -- guid рекламного предложения
            ``token`` -- токен (секретное значения для обеспечения уникальности ссылки)
        '''
        # TODO: Обновить документацию

        # Получаем словарь параметров
        param_lines = base64.urlsafe_b64decode(request.query_string).splitlines()
        params = dict([(x.partition('=')[0], x.partition('=')[2]) for x in param_lines])
        
        try:
            tasks.process_click.delay(url=params.get(url),
                                      ip=request.environ['REMOTE_ADDR'],
                                      click_datetime=datetime.datetime.now(),
                                      offer_id=params.get('id'),
                                      informer_id=params.get('inf'),
                                      token=params.get('token'),
                                      server=params.get('server'))
        except Exception, ex:
            tasks.process_click(url=params.get(url),
                                ip=request.environ['REMOTE_ADDR'],
                                click_datetime=datetime.datetime.now(),
                                offer_id=params.get('id'),
                                informer_id=params.get('inf'),
                                token=params.get('token'),
                                server=params.get('server'))
        
#        return "<br/>".join( [x[0] + " = " + x[1] for x in params.items()])
        return '''<html><body><script>window.location.replace('%s')</script></body></html>''' \
                % params.get('url', 'http://yottos.com')

