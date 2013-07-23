# coding: utf-8
from fabric.api import *
from pymongo import Connection

env.hosts = ['root@10.0.0.8']
env.passwords = {'root@10.0.0.8': 'cthdth$develop1'}

CONNECT_TO_MONGO = ['10.0.0.8:27017', '10.0.0.8:27018', '10.0.0.8:27019']

def deploy():
    with cd('/var/www/parser.yt'):
        run('svn up --force')
        run('rm -rf data/templates')
        run('chmod 777 -R *.ini')
        run('rm -rf /var/log/celeryd-parseryml.log')
        run('/etc/init.d/celeryd-parseryml restart')
    with cd('/var/www/rynok.yt'):
        run('svn up --force')
        run('chmod 777 -R *.ini')
        run('rm -rf /var/log/celeryd-rynok.log')
        run('/etc/init.d/celeryd-rynok restart')
    with cd('/var/www/manager.rynok.yt'):
        run('svn up --force')
        run('chmod 777 -R *.ini')
        run('rm -rf /var/log/celeryd-manager-rynok.log')
        run('/etc/init.d/celeryd-manager-rynok restart')
    with cd('/var/www/adload-rpc'):
        run('svn up --force')
        run('chmod 777 -R *.ini')
        run('rm -rf /var/log/celeryd-adload-rpc.log')
        run('/etc/init.d/celeryd-adload-rpc restart')
    run('rm -rf /var/log/apache2/*.log')
    run('/etc/init.d/apache2 reload')

def install():
    with cd('/var/www/parser.yt'):
        run('python setup.py install')
    with cd('/var/www/rynok.yt'):
        run('python setup.py install')
    with cd('/var/www/manager.rynok.yt'):
        run('python setup.py install')
    with cd('/var/www/adload-rpc'):
        run('python setup.py install')

def full_deploy():
    run('/etc/init.d/celeryd-parseryml stop')
    run('/etc/init.d/celeryd-rynok stop')
    run('/etc/init.d/celeryd-manager-rynok stop')
    run('/etc/init.d/celeryd-adload-rpc stop')

    run('/etc/init.d/rabbitmq-server start')
    run('rabbitmqctl stop_app')
    run('rabbitmqctl reset')
    run('/etc/init.d/rabbitmq-server stop')
    
    run('/etc/init.d/rabbitmq-server start')

    run('rabbitmqctl add_vhost rynok-rpc')
    run('rabbitmqctl add_user celery-rynok-rpc 123qwe')
    run('rabbitmqctl set_permissions -p rynok-rpc celery-rynok-rpc ".*" ".*" ".*"')

    run('rabbitmqctl add_vhost parser-rpc')
    run('rabbitmqctl add_user celery-parser-rpc 123qwe')
    run('rabbitmqctl set_permissions -p parser-rpc celery-parser-rpc ".*" ".*" ".*"')

    run('rabbitmqctl add_vhost adload-rpc')
    run('rabbitmqctl add_user celery-adload-rpc 123qwe')
    run('rabbitmqctl set_permissions -p adload-rpc celery-adload-rpc ".*" ".*" ".*"')

    run('rabbitmqctl add_vhost myvhost')
    run('rabbitmqctl add_user celery 123qwe')
    run('rabbitmqctl set_permissions -p myvhost celery ".*" ".*" ".*"')

    run('rabbitmqctl start_app')

    deploy()

    db_rynok = Connection(CONNECT_TO_MONGO)['rynok']
    db_rynok.Market.remove({}, safe=True)
    db_rynok.Advertise.remove({}, safe=True)
    db_rynok.Products.remove({}, safe=True)
    db_rynok.NewProducts.remove({}, safe=True)
    db_rynok.PopularProducts.remove({}, safe=True)
    db_rynok.clicks.remove({}, safe=True)
    db_rynok.clicks.error.remove({}, safe=True)
    db_rynok.clicks.rejected.remove({}, safe=True)
    db_rynok.blacklist.ip.remove({}, safe=True)
    
    categories_model = db_rynok.Category
    categories = categories_model.find({'count':{'$gt': 0}})
    for category in categories:
        categories_model.update({'ID':category['ID']}, {'$set':{'count':0}}, upsert=True)

    vendors_model = db_rynok.Vendors
    vendors = vendors_model.find({'count': {'$gt':0}})
    for vendor in vendors:
        vendors_model.update({'id': vendor['id']}, {'$set':{'count':0}}, upsert=True)
        
    db_parser = Connection(CONNECT_TO_MONGO)['parser']
    db_parser.Market.remove({}, safe=True)
    db_parser.Offers.remove({}, safe=True)
    db_parser.toParse.remove({}, safe=True)

    with cd('/var/www/parser.yt'):
        run('rm -rf parseryml/other/YML/*')
        run('rm -rf parseryml/other/OLD_YML/*')
        run('rm -rf parseryml/other/hashes/*')
        
    with cd('/var/www/cdnt.yt/images'):
        run('rm -rf *.jpg')
        run('rm -rf 128x80/*')
        run('rm -rf 213x168/*')
        run('rm -rf 98x83/*')
        run('rm -rf orig/*')

    db_adload = Connection(CONNECT_TO_MONGO)['adload']
    db_adload.AdvertisByProjects.remove({}, safe=True)

def parsing_stop():
    db_parser = Connection(CONNECT_TO_MONGO)['parser']
    markets = db_parser.Market.find({},{'id':1, 'state':1, 'status_id':1})
    for market in markets:
        if 'state' in market and 'state' in market['state'] and market['state']['state'] == 'parsing':

            print 'Manual Stop: %s' % (market['id'])

            db_parser.Market.update({'id':market['id']}, {"$set":{'state':{
                'state':'error',
                'message':'Перезапущено вручную'
            }}})
            db_parser.Market.update({'id':market['id']}, {"$set":{'status_id':2}})
