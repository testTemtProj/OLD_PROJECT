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
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    #static routes
    map.connect('yottos.com', "http://yottos.com", _static=True)

    #map.connect('/redirect/get_banner/{category}')
    map.connect('/manager/', controller='manager', action='login', sub_domain='manager')
    map.connect('/manager/{action}', controller='manager', sub_domain='manager')
    map.connect('/manager/sites/{category_id}', controller='manager', action='sites', requirements={'category_id':'[0-9]*'})
    map.connect('/category/search/{page}',controller='category', action='search', requirements={'page':'[0-9]+'})
    map.connect('/', controller='category',action='index', page=1)
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')



    map.connect('/*category/{page}', controller='category', action='index', requirements={'category':'[A-Za-z_/0-9]+', 'page':'[0-9]+'})
    map.connect('/*category', controller='category', action='index', page=1, requirements={'category':'[A-Za-z_/0-9]+'})



    return map
