##﻿# encoding: utf-8
import logging

from pylons import  app_globals
#from pylons.controllers.util import abort, redirect
from pylons.controllers import XMLRPCController

log = logging.getLogger(__name__)
from parseryml.lib.tasks import parse_by_id, market_test_task, parse_by_url


class RpcController(XMLRPCController):
    'Класс предоставляет XML-RPC интерфейс для взаимодействия и управления ``ParserYML``'

    def parse_shop(self, shop_id):
        """
        Добавление задачи на распарсивание  
        """
        if shop_id.isdigit():
            parse_by_id.delay(int(shop_id))
            return {'ok':True}
        else:
            return {'ok':False}
        
    parse_shop.signature = [['struct', 'string']]

   
    def get_shop_categories(self, shop_id):
        """"Возвращает категории магазина"""
        if not shop_id.isdigit():
            return {'error':True, 'msg': u'shop_id должен быть цифровой строкой'}

        categories = []
        state = {'error':False}        
        market = app_globals.db.Market.find_one({"id":int(shop_id)})

        if market is None:
            state = {'error':True, 'msg':u'Магазина %s в базе нет' % (shop_id)}
        else:
            if len(market['Categories']) == 0:
                try:
                    parse_task = parse_by_id.delay(int(shop_id))
                    parse_task.wait()
                    parse_task.get()
                    market = app_globals.db.Market.find_one({"id":int(shop_id)})
                    categories = market['Categories']
                except Exception, ex:
                    state = {'error':True, 'msg':str(ex)}
            else:
                categories = market['Categories']

        return {'categories':categories, 'state':state}
                        
    get_shop_categories.signature = [['struct', 'string']]

    def market_yml_test(self, url):
        """
        Проверка на валидность файла-выгрузки
        """
        t = market_test_task.delay(url)
        t.wait()
        r = t.get()
        return r
    market_yml_test.signature = [['struct', 'string']]
        
