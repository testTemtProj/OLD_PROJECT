# This file uses following encoding: utf-8
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from parseryml.lib.base import BaseController, render
import os
import ConfigParser
import xmlrpclib

PYLONS_CONFIG = "development.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config = ConfigParser.ConfigParser()
config.read(config_file)
#LOG = logging.getLogger(__name__)
RYNOK_XMLRPC_HOST = config.get('app:main', 'rynok_xmlrpc_server')
class WebRpcController(BaseController):
    def index(self):
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.server_status()
        rynok_ok = rynok_response.get('ok', False)
        print rynok_ok
        return str(rynok_ok)
    
    def get_offers(self):
        """Получение предложений магазина"""        
        id = request.params.get("id", False)
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.get_offers_market_by_id(id)
        rynok_ok = rynok_response.get('ok', False)
        return str(rynok_ok)
    
    def get_update_offers(self):
        """Инкрементное получение предложений магазина"""        
        id = request.params.get("id", False)
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.get_offers_market_by_id(id)
        rynok_ok = rynok_response.get('ok', False)
        return str(rynok_ok)
    def add(self):
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.add_market(1)
        rynok_ok = rynok_response#.get('ok', False)
        return str(rynok_ok)

    def start(self):
        id = 1        
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.start_market(id)
        rynok_ok = rynok_response.get('ok', False)        
        return str(rynok_ok)

    def stop(self):
        id = 1
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.stop_market(id)
        rynok_ok = rynok_response.get('ok', False)
        return str(rynok_ok)

    def delete(self):
        id = 1
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.remove_market(id)
        rynok_ok = rynok_response.get('ok', False)
        return str(rynok_ok)

    def parse(self):
        """Парсинг магазина"""        
        url = request.params.get("url", "")
        rynok = xmlrpclib.ServerProxy(RYNOK_XMLRPC_HOST)
        rynok_response = rynok.to_parse_market(url)
        rynok_ok = rynok_response.get('ok', False)
        return str(rynok_ok)
