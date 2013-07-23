# encoding: utf-8
import base64
import datetime
from getmyad.tasks import tasks


def redirect(environ, start_response):
    response_headers = [('Content-type','text/html')]
    start_response("200 OK", response_headers)
    
    # Получаем словарь параметров
    param_lines = base64.urlsafe_b64decode(environ['QUERY_STRING']).splitlines()
    params = dict([(x.partition('=')[0], x.partition('=')[2]) for x in param_lines])
    
    try:
        tasks.process_click.delay(url=params.get('url'),
                                  ip=environ['REMOTE_ADDR'],
                                  click_datetime=datetime.datetime.now(),
                                  offer_id=params.get('id'),
                                  informer_id=params.get('inf'),
                                  token=params.get('token'),
                                  server=params.get('server'))
    except Exception, ex:
        tasks.process_click(url=params.get('url'),
                            ip=environ['REMOTE_ADDR'],
                            click_datetime=datetime.datetime.now(),
                            offer_id=params.get('id'),
                            informer_id=params.get('inf'),
                            token=params.get('token'),
                            server=params.get('server'))

    
    response = '''<html><body><script>window.location.replace('%s')</script></body></html>'''
    response %= params.get('url', 'http://yottos.com')
    return [response]


application = redirect