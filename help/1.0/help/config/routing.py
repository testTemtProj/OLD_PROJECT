"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False
    map.explicit = False
    map.sub_domains = True
    map.sub_domains_ignore = ['www']
    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error',conditions={'sub_domain':True})
    map.connect('/error/{action}/{id}', controller='error',conditions={'sub_domain':True})

    # CUSTOM ROUTES HERE
    map.connect('/', controller='main',action='index',conditions={'sub_domain':None})
    map.connect('/', controller='getmyad',action='index',conditions={'sub_domain':['getmyad',]})
    map.connect('/', controller='clevad',action='index',conditions={'sub_domain':['clevad',]})
    map.connect('/about', controller='main',action='about',conditions={'sub_domain':None})
    map.connect('/about', controller='getmyad',action='about',conditions={'sub_domain':['getmyad',]})
    map.connect('/about', controller='clevad',action='about',conditions={'sub_domain':['clevad',]})
    map.connect('/news', controller='main',action='news',conditions={'sub_domain':None})
    map.connect('/news', controller='getmyad',action='news',conditions={'sub_domain':['getmyad',]})
    map.connect('/news', controller='clevad',action='news',conditions={'sub_domain':['clevad',]})
    map.connect('/news/{page}', controller='main',action='news',requirements={'page':'[0-9]+'},conditions={'sub_domain':None})
    map.connect('/news/{page}', controller='getmyad',action='news',requirements={'page':'[0-9]+'},conditions={'sub_domain':['getmyad',]})
    map.connect('/news/{page}', controller='clevad',action='news',requirements={'page':'[0-9]+'},conditions={'sub_domain':['clevad',]})
    map.connect('/news/{page}/{id}', controller='main',action='news',requirements={'page':'[0-9]+','id':'[0-9]+'},conditions={'sub_domain':None})
    map.connect('/news/{page}/{id}', controller='getmyad',action='news',requirements={'page':'[0-9]+','id':'[0-9]+'},conditions={'sub_domain':['getmyad',]})
    map.connect('/news/{page}/{id}', controller='clevad',action='news',requirements={'page':'[0-9]+','id':'[0-9]+'},conditions={'sub_domain':['clevad',]})
    map.connect('/rules', controller='main',action='rules',conditions={'sub_domain':None})
    map.connect('/rules', controller='getmyad',action='rules',conditions={'sub_domain':['getmyad',]})
    map.connect('/rules', controller='clevad',action='rules',conditions={'sub_domain':['clevad',]})
    map.connect('/rules/{date}', controller='main',action='rules',conditions={'sub_domain':None},requirements={'date':'[-0-9]+'})
    map.connect('/rules/{date}', controller='getmyad',action='rules',conditions={'sub_domain':['getmyad',]},requirements={'date':'[-0-9]+'})
    map.connect('/rules/{date}', controller='clevad',action='rules',conditions={'sub_domain':['clevad',]},requirements={'date':'[-0-9]+'})
    map.connect('/search', controller='main',action='search',conditions={'sub_domain':None})
    map.connect('/search', controller='getmyad',action='search',conditions={'sub_domain':['getmyad',]})
    map.connect('/search', controller='clevad',action='search',conditions={'sub_domain':['clevad',]})
    map.connect('/search/{page}', controller='main',action='search',requirements={'page':'[0-9]+'},conditions={'sub_domain':None})
    map.connect('/search/{page}', controller='getmyad',action='search',requirements={'page':'[0-9]+'},conditions={'sub_domain':['getmyad',]})
    map.connect('/search/{page}', controller='clevad',action='search',requirements={'page':'[0-9]+'},conditions={'sub_domain':['clevad',]})
    map.connect('/help', controller='main',action='help',conditions={'sub_domain':None})
    map.connect('/help', controller='getmyad',action='help',conditions={'sub_domain':['getmyad',]})
    map.connect('/help', controller='clevad',action='help',conditions={'sub_domain':['clevad',]})
    map.connect('/{controller}/{action}', conditions={'sub_domain':None})
    map.connect('/{controller}/{action}/{id}', conditions={'sub_domain':None})
    map.connect('/', controller='main',action='index',conditions={'sub_domain':True})
    map.connect('/{controller}/{action}', conditions={'sub_domain':True})
    map.connect('/{controller}/{action}/{id}', conditions={'sub_domain':True})

    map.connect('/help/*category', controller='main', action='help', requirements={'category':'[a-za-z_/0-9]+'},conditions={'sub_domain':None})
    map.connect('/help/*category', controller='getmyad', action='help', requirements={'category':'[a-za-z_/0-9]+'},conditions={'sub_domain':['getmyad',]})
    map.connect('/help/*category', controller='clevad', action='help', requirements={'category':'[a-za-z_/0-9]+'},conditions={'sub_domain':['clevad',]})

    return map
