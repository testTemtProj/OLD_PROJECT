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

    
    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    map.connect('/search/', page=1, cat_url='', controller='search', action='index', requirements={'page':'[0-9]+'})
    map.connect('/search/{page}', page=1, cat_url='', controller='search', action='index', requirements={'page':'[0-9]+'})
    map.connect('/search/*cat_url/{page}', page=1, cat_url='', controller='search', action='index', requirements={'page':'[0-9]+', 'cat_url':'[A-Za-z_/0-9]+'})
    map.connect('/search/*cat_url', page=1, cat_url='', controller='search', action='index', requirements={'page':'[0-9]+', 'cat_url':'[A-Za-z_/0-9]+'})
    map.connect('/{controller}/{action}')
    #map.connect('/{controller}/{action}/{id}')
    

    #map.connect('/search/', cat_url='', controller='search', action='index', requirements={'page':'[0-9]+'})
    map.connect('main_page', '/', controller='main', action='index')
    map.connect('/new', controller='category', action='new')
    map.connect('/popular', controller='category', action='popular')
    map.connect('static_pages', '/{static_page_slug}.html', controller='static', action='view', requirments={'slug': '[.[A-Za-z_0-9/]+'})
    map.connect('new_products', '/new_products', controller='new_products', action='index')
    map.connect('popular_products', '/popular_products', controller='popular_products', action='index')
    map.connect('/vendor/{vendor}/', page=1, cat_url='', controller='vendor', action='index', requirements={'vendor':'[-A-Za-z_0-9]+', 'page':'[0-9]+'})
    map.connect('/vendor/{vendor}/{page}', cat_url='', controller='vendor', action='index', requirements={'vendor':'[-A-Za-z_0-9]+', 'page':'[0-9]+'})
    map.connect('/vendor/{vendor}/*cat_url/', page=1, controller='vendor', action='index', requirements={'vendor':'[-A-Za-z_0-9]+', 'page':'[0-9]'})
    map.connect('/vendor/{vendor}/*cat_url/{page}', controller='vendor', action='index', requirements={'vendor':'[-A-Za-z_0-9]+', 'page':'[0-9]'})
    map.connect('/market/{market}/', cat_url='', page=1, controller='market', action='index', requirements={'market':'[A-Za-z-0-9]+', 'page':'[0-9]+'})
    map.connect('/market/{market}/{page}', cat_url='', controller='market', action='index', requirements={'market':'[A-Za-z-0-9]+', 'page':'[0-9]+'})
    map.connect('/market/{market}/*cat_url/{page}', controller='market', action='index', requirements={'market':'[A-Za-z-0-9]+', 'page':'[0-9]+'})
    map.connect('/market/{market}/*cat_url/', page=1, controller='market', action='index', requirements={'market':'[A-Za-z-0-9]+', 'page':'[0-9]+'})
    #map.connect('/{product_title}/{product_id}.html', controller='product', action='index', requirements={'product_title':'[A-Za-z_0-9]+', 'product_id': '[0-9]+'})
    map.connect('/*url/', controller='category', action='index', requirements={'url':'[A-Za-z_/0-9]+'}, page=0)
    map.connect('/*category/{page}', controller='category', action='view', requirements={'category':'[A-Za-z_/0-9]+', 'page':'[0-9]+'})

    return map
