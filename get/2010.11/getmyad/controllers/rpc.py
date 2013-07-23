# This file uses following encoding: utf-8
from amqplib import client_0_8 as amqp
from getmyad.lib.base import render
from getmyad.model import Campaign, Offer, mq
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

class RpcController(XMLRPCController):
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
        
        details = app_globals.adload_rpc.campaign.details(campaign_id)

        # Если кампании уже нет в AdLoad или она помечена как запрещённая для показа в getmyad,
        # останавливаем её в GetMyAd
        if not details or not details.get('getmyad'):
            result_stop = self.campaign_stop(campaign_id)
            return u"Кампания не запущена в AdLoad или запрещена для показа в GetMyAd. \n" + \
                    u"Останавливаю кампанию: %s" % result_stop

        camp.title = details['title']
        camp.last_update = datetime.datetime.now() 
        camp.save()
        
        offers = app_globals.adload_rpc.offers.list(campaign_id)
        app_globals.db.offer.remove({'campaignId': campaign_id}, safe=True)
        for x in offers:
            offer = Offer(x['id'])
            offer.title = x['title']
            offer.price = x['price']
            offer.url = x['url']
            offer.image = self.resize_and_upload_image(x['image'], 120, 120)
            offer.description = x['description']
            offer.date_added = x['dateAdded']
            offer.campaign = campaign_id
            offer.save()
            
        if not offers:
            # Если у кампании нет товарных предложний, это скорее всего значит,
            # что на счету закончились деньги
            result_stop = self.campaign_stop(campaign_id) 
            return u"В кампании нет активных предложений. \n" + \
                    u"Возможные причины: на счету кампании нет денег, не отработал парсер Рынка (для интернет-магазинов).\n" + \
                    u"Останаваливаю кампанию: %s" % result_stop

        mq.MQ().campaign_update(campaign_id)         
        return 'ok'
    campaign_update.signature = [['string', 'string']]
    
    
    def campaign_list(self):
        ''' Возвращает список всех запущенных в GetMyAd кампаний.
        ''' # TODO: Дописать документацию
        
        result = []
        for x in app_globals.db.campaign.find():
            campaign = {'id': x.get('guid'),
                        'title': x.get('title')}
            result.append(campaign)
        return result
    campaign_list.signature = [['array']]
    
    def resize_and_upload_image(self, url, height, width):
        ''' Пережимает изображение по адресу ``url`` до размеров
            ``height``x``width`` и заливает его на ftp для раздачи статики.
            Возвращает url нового файла или пустую строку в случае ошибки.
        '''
        try:
            if not config.get('cdn_server_url') or not config.get('cdn_ftp'):
                log.warning('Не заданы настройки сервера CDN. Проверьте .ini файл.')
                return ''
            size_key = '%sx%s' % (height,width)
            rec = app_globals.db.image.find_one({'src': url, size_key: {'$exists': True}})
            if rec:
                return rec[size_key].get('url')
            
            f = urllib.urlretrieve(url)[0]
            i = Image.open(f)
            i.thumbnail((height, width), Image.ANTIALIAS)
            buf = StringIO.StringIO()
            i.save(buf, 'JPEG')
            buf.seek(0)
            new_filename = uuid1().get_hex() + '.jpg'
            ftp = ftplib.FTP(host=config.get('cdn_ftp'))
            ftp.login(config.get('cdn_ftp_user'), config.get('cdn_ftp_password'))
            ftp.cwd(config.get('cdn_ftp_path'))
            ftp.cwd('img')
            ftp.storbinary('STOR %s' % new_filename, buf)
            new_url = config.get('cdn_server_url') + 'img/' + new_filename
            app_globals.db.image.ensure_index('src')
            app_globals.db.image.update({'src': url},
                                        {'$set': {size_key: {'url': new_url,
                                                             'w': width,
                                                             'h': height,
                                                             'realWidth': i.size[0],
                                                             'realHeight': i.size[1],
                                                             'dt': datetime.datetime.now()
                                                             }}},
                                        upsert=True, safe=True)
            return new_url
        except Exception as ex:
            log.exception(ex)
            return ''
    resize_and_upload_image.signature = [['string', 'string', 'int', 'int']]

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
        for i in app_globals.db.informer.find({}, fields=['guid']):
            InformerFtpUploader(i['guid']).upload_reserve()
              
    