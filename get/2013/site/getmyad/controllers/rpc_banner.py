# This file uses following encoding: utf-8
from amqplib import client_0_8 as amqp
from getmyad.lib.base import render
from getmyad.model.Campaign import Campaign
from getmyad.model.Offer import Offer
from getmyad.model import mq
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals, config
from pylons.controllers import XMLRPCController
from pylons.controllers.util import abort, redirect
from uuid import uuid1
import Image
import StringIO
import datetime
import ftplib
import logging
import urllib

log = logging.getLogger(__name__)

class RpcBannerController(XMLRPCController):
    ''' Предоставляет XML-RPC интерфейс управления и взаимодействия с GetMyAd '''
    
    
    def server_status(self):
        ' Состояние сервера и некоторая статистика GetMyAd'
        res = {'ok': True,
               'camapaigns': app_globals.db.campaign.find().count(),
               'offers': app_globals.db.offer.find().count()}
        return res
    server_status.signature = [['struct']]
        
    
    def campaign_start(self, campaign_id):
        """ Запуск рекламной кампании ``campaign_id`` в GetMyAd.
        
        У кампании должно быть разрешение рекламу в GetMyAd *(см. методы AdLoad API
        campaign.addToGetMyAd и campaign.removeFromGetmyad)*.
        
        Для получения всей информации метод обращается к AdLoad. В процессе работы создаётся
        кампания и загружаются её рекламные предложения. Если кампания уже была запущена ранее,
        а затем остановлена, настройки её будут восстановлены из архива (коллеция 
        ``campaign.arhive``).
        
        Если кампания уже запущена, метод вернёт сообщение об этом и ничего не сделает.
        """
        campaign_id = campaign_id.lower()
        camp = Campaign(campaign_id)
        camp.project = 'banner'
        if camp.exists():
            return "Campaign is already running, try to stop it first"
        camp.restore_from_archive()
        if not camp.exists():
            camp.save()                                     # Сохраняем пустую кампанию
        update_result = self.campaign_update(campaign_id)   # ...и загружаем её реальными значениями
        if update_result == "ok":
            mq.MQ().campaign_start(campaign_id)             # Отправляем сообщение о запуске кампании
            return "ok"
        else:
            return update_result
    campaign_start.signature = [['string', 'string']]
    
    
    def campaign_stop(self, campaign_id):
        ''' Остановка рекламной кампании ``campaign_id`` в GetMyAd '''
        campaign_id = campaign_id.lower()
        camp = Campaign(campaign_id)
        camp.move_to_archive()
        app_globals.db.offer.remove({'campaignId': campaign_id}, safe=True)
        app_globals.db.stats_daily.rating.remove({'campaignId': campaign_id}, safe=True)
        mq.MQ().campaign_stop(campaign_id)  # Отправляем сообщение 
        return "ok"
    campaign_stop.signature = [['string', 'string']]
    
    
    def campaign_update(self, campaign_id):
        ''' Обновляет рекламную кампанию ``campaign_id``.
        
        При обновлении происходит получение от AdLoad нового списка предложений и
        общей информации о кампании.
        
        Если кампания не была запущена, ничего не произойдёт.
        
        Если в кампании нет активных предложений, она будет остановлена.
        '''
        campaign_id = campaign_id.lower()
        camp = Campaign(campaign_id)
        
        try:
            camp.load()
        except Campaign.NotFoundError:
            return 'Campaign is not running'
        
        details = app_globals.db.banner.campaign.find_one({'guid':campaign_id})
        camp.title = details['title']
        camp.project = 'banner'
        camp.last_update = datetime.datetime.now() 
        camp.save()
        offers = []
        curs = app_globals.db.banner.offer.find({'campaignId':campaign_id})
        for item in curs:
            offers.append({'id':item['guid'],
                           'title':item['title'],
                           'imp_cost':item['imp_cost'],
                           'price':0,
                           'url':item['url'],
                           'image':item.get('image',None),
                           'swf':item.get('swf',None),
                           'description':'',
                           'dateAdded':item['dateAdded'],
                           'type':item['type'],
                           'width':item['width'],
                           'height':item['height']
                           })

        if not offers:
            # Если у кампании нет товарных предложний, это скорее всего значит,
            # что на счету закончились деньги
            result_stop = self.campaign_stop(campaign_id) 
            return u"В кампании нет активных предложений. \n" + \
                    u"Возможные причины: не привязаны банеры.\n" + \
                    u"Останаваливаю кампанию: %s" % result_stop

        app_globals.db.offer.remove({'campaignId': campaign_id, 'hash':{'$exists' : False}}, safe=True)
        hashes = app_globals.db.offer.group(key={'hash':True}, condition={'hash': {'$exists': True}, 'campaignId': campaign_id}, reduce='function(obj,prev){}', initial={})
        hashes = map(lambda x: x['hash'], hashes)
        ctr = 1
        uniqueHits_campaign = camp.UnicImpressionLot
        campaignTitle = camp.title
        for x in offers:
            offer_cost = float(x.get('imp_cost', '0.0'))
            offer = Offer(x['id'])
            offer.title = x['title']
            offer.price = x['price']
            offer.url = x['url']
            offer.campaignTitle = campaignTitle
            offer.image = x['image']
            offer.swf = x['swf']
            offer.description = x['description']
            offer.date_added = x['dateAdded']
            offer.campaign = campaign_id
            offer.listAds = ['ALL']
            offer.isOnClick = False
            offer.type = x['type']
            offer.uniqueHits = uniqueHits_campaign
            offer.width = int(x['width'])
            offer.height = int(x['height'])
            offer.rating = round(((1 * offer_cost)* 100000), 4)
            offer.cost = offer_cost
            offer.hash = offer.createOfferHash()
            if offer.hash not in hashes:
                offer.save()
            else:
                offer.update()
                hashes.remove(offer.hash)

        app_globals.db.offer.remove({'campaignId': campaign_id, 'hash':{'$in' : hashes}}, safe=True)
            
        mq.MQ().campaign_update(campaign_id)         
        return 'ok'
    campaign_update.signature = [['string', 'string']]
    
    
    def campaign_list(self):
        ''' Возвращает список всех запущенных в GetMyAd кампаний.
        ''' # TODO: Дописать документацию
        
        result = []
        for x in app_globals.db.campaign.find({"project": "banner"}):
            campaign = {'id': x.get('guid'),
                        'title': x.get('title')}
            result.append(campaign)
        return result
    campaign_list.signature = [['array']]
    

    def campaign_details(self, campaign_id):
        ''' Возвращает состояние кампании ``campaign_id``.
        
        Ответ имеет следующий формат::
        
            (struct)
                'id': (string)
                'title': (string)
                'status': (string)
                'offersCount': (int)
                'lastUpdate': (datetime)
            (struct-end)
        
        
        Поля ``id``и ``title`` обозначают id и наименование кампании соответственно.
        Количество запущенных предложений находится в ``offersCount``. Время последней
        синхронизации с AdLoad --- ``lastUpdate``.
         
        Поле ``status`` обозначает состояние кампании и может принимать следующие значения:
        
        +---------------+---------------------------------------------------------------+
        |     status    |  Описание                                                     | 
        +===============+===============================================================+
        | ``not_found`` |  Кампания не была запущена в GetMyAd, либо такой кампании не  |
        |               |  существует в принципе. Вернутся только поля ``id`` и         |
        |               |  ``status``.                                                  |
        +---------------+---------------------------------------------------------------+
        |  ``working``  |  Кампания запущена и работает в данный момент.                |
        |               |                                                               |
        +---------------+---------------------------------------------------------------+
         
        '''
        campaign_id = campaign_id.lower()
        c = Campaign(campaign_id)
        if not c.exists():
            return {'status': 'not_found'}
        c.load()
        offers_count = app_globals.db.offer.find({'campaignId': campaign_id}).count()
        
        
        return {'id': c.id,
                'title': c.title,
                'status': 'working',
                'offersCount': offers_count,
                'lastUpdate': c.last_update
                }
    
    
    def maintenance_uploadEmergencyAds(self):
        ''' Загружает аварийные заглушки для всех информеров '''
        from getmyad.model import InformerFtpUploader
        uploaded_count = 0
        failed_count = 0
        for i in app_globals.db.informer.find({}, fields=['guid']):
            try:
                InformerFtpUploader(i['guid']).upload_reserve()
                uploaded_count += 1
            except:
                failed_count += 1
        return {'uploaded_informers': uploaded_count, 'failed': failed_count}

    def maintenance_uploadInformerLoaders(self):
        ''' Загружает javascript загрузчики для всех информеров '''
        from getmyad.model import InformerFtpUploader
        uploaded_count = 0
        failed_count = 0
        for i in app_globals.db.informer.find({}, fields=['guid']):
            try:
                InformerFtpUploader(i['guid']).upload_loader()
                uploaded_count += 1
            except:
                failed_count += 1
        return {'uploaded_informers': uploaded_count, 'failed': failed_count}
