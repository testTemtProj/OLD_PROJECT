# This file uses following encoding: utf-8
from pylons import app_globals, config

from pylons.controllers import XMLRPCController
from manager.model.campaignsModel import CampaignsModel
from datetime import datetime

#log = logging.getLogger(__name__)
class RpcController(XMLRPCController):
    def server_status(self):
        """Возвращает общее состояние рынка"""
        res = {'ok': True}
        return res
    server_status.signature = [['struct']]
    
    
    def update_advertise_by_id(self, campaign_id):
        #TODO разобраться с сообщениями
        campaigns_model = CampaignsModel             
        return campaigns_model.update_campaign(campaign_id)
    update_advertise_by_id.signature = [['struct', 'string']]
        
        
    def add_market(self, id):
        """Добавления магазина на рынок"""
        res = {'ok': True}        
        return res
    add_market.signature = [['struct', 'int']]


    def remove_market(self, market_id):
        """Удаление магазина на рынок"""
        res = {'ok': True}
        return res
    remove_market.signature = [['struct']]


    def start_market(self, market_id): 
        """Запуск магазина на рынке"""
        res = {'ok': True}
        return res
    start_market.signature = [['struct']]


    def stop_market(self, market_id):
        """Остановка магазина на рынке"""
        res = {'ok': True}
        return res
    stop_market.signature = [['struct']]

    
    def to_parse_market(self, url):
        """Отправка магазина на распарсивание"""
        res = {'ok':True}
        return res
    to_parse_market.signature = [['struct']]
