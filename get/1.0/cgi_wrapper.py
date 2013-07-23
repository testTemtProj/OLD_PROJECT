from paste.deploy import loadapp




def simple_app(environ, start_response):
    """Simplest possible application object"""
#    status = '200 OK'
#    response_headers = [('Content-type','text/plain')]
#    start_response(status, response_headers)

    appdir = 'G:/www/pylons/env/projects/getmyad/'
    wsgi_app = loadapp('config:' + appdir + 'deploy.ini', relative_to=appdir)
    environ['SCRIPT_NAME'] = ''
    return wsgi_app(environ, start_response)


import wsgiref.handlers
wsgiref.handlers.CGIHandler().run(simple_app)
