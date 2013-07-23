# encoding: utf-8
import logging

from pylons import request, response, session, tmpl_context as c, url,\
    app_globals
from pylons.controllers.util import abort, redirect
from pylons.controllers import XMLRPCController
import datetime
import uuid
import dateutil.parser
import xmlrpclib
from adload.lib.tasks import get_offers_task
from adload.lib.tasks import get_category_market
from adload.lib.base import BaseController, render

log = logging.getLogger(__name__)

import os
import ConfigParser
PYLONS_CONFIG = "development.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config = ConfigParser.ConfigParser()
config.read(config_file)
#LOG = logging.getLogger(__name__)
PARSER_XMLRPC_HOST = config.get('app:main', 'parser_xmlrpc_server')

class RpcController(XMLRPCController):
    'Класс предоставляет XML-RPC интерфейс для взаимодействия и управления ``AdLoad``'
    def arr(self, x):        
        return range(x)
    arr.signature = [['array', 'int']]    
    def get_shop_by_advertise(self, advertise):
        """
        Возвращает список магазинов по ид рекламной кампании
        """
        cursor = app_globals.connection_adload.cursor()
        cursor.execute("""
        SELECT UserID, m.MarketID, MarketID_int, a.MarketID, a.AdvertiseID as AdvertiseID
          FROM Market m
          inner join MarketByAdvertise a on a.MarketID=m.MarketID
          where AdvertiseID ='%s'
        """ %(advertise))
        #shopId = cursor.fetchone().MarketID_int
        #row = cursor.fetchone()
        res = []
        for row in cursor:            
            res.append(row.MarketID_int)
        return res
    get_shop_by_advertise.signature = [['array', 'string']]
    
    def offers_list(self, campaign):
        """ Возвращает список активных рекламных предложений,
            относящихся к рекламной кампании ``campaign``. 

            Ответ имеет следующий формат::

                (array)
                    (struct)
                        'id':          (string),
                        'title':       (string),
                        'price':       (string),
                        'url':         (string),
                        'image':       (string),
                        'description': (string),
                        'dateAdded':   (string)
                    (struct-end)
                (array-end)
        
         """
        try:
            #cursor = app_globals.connection_rynok.cursor()
            offers = []
            
#            # Предложения с Рынка (интернет-магазины)
                
            # Частные предложения (информеры)
            cursor = app_globals.connection_adload.cursor()
            query = '''
                select Lot.LotID LotID, Lot.Title Title, ExternalURL UrlToMarket, 
                    isnull(Lot.Descript, '') as About,
                    case when LotPhoto.PhotoID is null
                    then '' 
                    else 'http://rynok.yottos.com/photo.aspx?id=' + cast(LotPhoto.PhotoID as varchar(50))
                    end as ImgURL
                    ,ISNULL(lot.Price, '') Price
                    ,Lot.DateCreate as DateAdvert
                from Lot 
                inner join LotByAdvertise on LotByAdvertise.LotID = Lot.LotID 
                left outer join LotPhoto on LotPhoto.LotID = Lot.LotID
                where LotByAdvertise.AdvertiseID = '%s' and Lot.ExternalURL <> '' 
                    and Lot.isTest = 1 and lot.isAdvertising = 1
                ''' %(campaign)            
            cursor.execute(query)
            for row in cursor:
                offer = {'id': str(row.LotID).lower(),
                         'title': row.Title,
                         'price': row.Price,
                         'url': row.UrlToMarket,
                         'image': row.ImgURL,
                         'description': row.About.decode('cp1251'),
                         'dateAdded': row.DateAdvert
                        }
                offers.append(offer)

            return {"offers":offers}
        except Exception, ex:            
            return {"Error":"Server-side exception has occured: " + str(ex)}
    offers_list.signature = [['struct', 'string']]

    def get_offers(self, campaign):        
        print "get_offers_from_rynok"
        cursor = app_globals.connection_adload.cursor()
        cursor.execute("""
        SELECT UserID, m.MarketID, MarketID_int, a.MarketID, a.AdvertiseID as AdvertiseID
          FROM Market m
          inner join MarketByAdvertise a on a.MarketID=m.MarketID
          where AdvertiseID ='%s'
        """ %(campaign))
        shopId = cursor.fetchone().MarketID_int
        try:
            task = get_offers_task.delay(shopId)
            task.wait()
            return task.result
        except:
            return get_offers_task(shopId)

    get_offers.signature = [['struct', 'string']]
    def get_offers_page(self, campaign, page):        
        print "get_offers_from_rynok"
        cursor = app_globals.connection_adload.cursor()
        cursor.execute("""
        SELECT UserID, m.MarketID, MarketID_int, a.MarketID, a.AdvertiseID as AdvertiseID
          FROM Market m
          inner join MarketByAdvertise a on a.MarketID=m.MarketID
          where AdvertiseID ='%s'
        """ %(campaign))
        shopId = cursor.fetchone().MarketID_int
        try:
            task = get_offers_task.delay(shopId, page)
            task.wait()
            return task.result
        except:
            return get_offers_task(shopId, page)

    get_offers_page.signature = [['struct', 'string', 'int']]    
    def update_offers(self, campaign):        
        print "update_offers"
        parser = xmlrpclib.ServerProxy(PARSER_XMLRPC_HOST)        
        cursor = app_globals.connection_adload.cursor()
        cursor.execute("""
        SELECT UserID, m.MarketID, MarketID_int, a.MarketID, a.AdvertiseID as AdvertiseID
          FROM Market m
          inner join MarketByAdvertise a on a.MarketID=m.MarketID
          where AdvertiseID ='%s'
        """ %(campaign))
        shopId = cursor.fetchone().MarketID_int
        print shopId
        parser_response = parser.get_update_market_by_id(shopId)        
        return parser_response
    update_offers.signature = [['struct', 'string']]    
    
    def get_offers_market_by_id(self, id):
        print "get_offers_market_by_id"
        parser = xmlrpclib.ServerProxy(PARSER_XMLRPC_HOST)        
        parser_response = parser.get_offers_market_by_id(id)
        if parser_response.has_key("offers"):
            return parser_response["offers"]
        else:
            return []
    get_offers_market_by_id.signature = [['array', 'int']]    
    
    def get_category_market_by_id(self, shopId):
        """Получение категорий магазина"""        
        print "get_category_market_by_id"
        parser = xmlrpclib.ServerProxy(PARSER_XMLRPC_HOST)        
        parser_response = parser.get_category_market_by_id(int(shopId))
        print parser_response     
        return parser_response
        try:                
            task = get_category_market.delay(shopId)
            task.wait(10)
            return task.result
        except:
            return get_category_market(shopId)               
        
    get_category_market_by_id.signature = [['struct', 'int']]   
   
    def advertise_list(self):
        """Возвращает список всех активных рекламных кампаний.
        
        Ответ имеет следующий формат::

            (array)
                (struct)
                    'id':      (string)
                    'user':    (string)
                    'title':   (string)
                    'getmyad': (bool) 
                (struct-end)
            (array-end)
        
        ``getmyad`` показывает, рекламируется ли кампания в GetMyAd или нет.
        """
        cursor = app_globals.connection_adload.cursor()
        cursor.execute('''select a.AdvertiseID as AdvertiseID, a.UserID as UserID, Title, 
                            case when ag.AdvertiseID is null then 0 else 1 end as InGetMyAd,
                            au.UserID,
                            au.Login as Login,                        
                            a.isActive as isActive                            
                        from Advertise a
                        inner join Users au on au.UserID = a.UserID                        
                        left outer join AdvertiseInGetMyAd ag on ag.AdvertiseID = a.AdvertiseID
                        order by Title''')
        result = []
        for row in cursor:
            try:
                title = row.Title.decode('cp1251')
            except:
                title = row.Title            
            adv = {'id': str(row.AdvertiseID).lower(),
                   'user': str(row.UserID).lower(),
                   'login':row.Login.decode('cp1251'),                  
                   'state':row.isActive,
                   'title': title
                  }
            result.append(adv)        
        return result
    advertise_list.signature = [['array']]
    
    
    def campaign_details(self, campaign):
        ''' Возвращает подробную информацию о кампании ``campaign``.
        Формат ответа::
            
            (struct)
                'id':      (string)
                'title':   (string)
                'getmyad': (bool)
            (struct-end)
        '''
        cursor = app_globals.connection_adload.cursor()
        cursor.execute('''select a.AdvertiseId as AdvertiseID, UserID, Title, 
                            case when ag.AdvertiseID is null then 0 else 1 end as InGetMyAd
                        from Advertise a
                        left outer join AdvertiseInGetMyAd ag on ag.AdvertiseID = a.AdvertiseID
                        where a.AdvertiseID = %s''', campaign)
        row = cursor.fetchone()
        if not row:
            return {}
        return {'id': str(row.AdvertiseID).lower(),
                'title': row.Title.decode('cp1251'),
                'getmyad': bool(row.InGetMyAd)
                }
    campaign_details.signature = [['struct', 'string']]
    

    
    def campaign_add(self, project, campaign_id):
        ''' Добавляет кампанию ``campaign_id`` в список кампаний, которые должны рекламироваться  '''
        rynok=False
        getmyad=False
        if project=="rynok":
            rynok=True
        if project=="getmyad":
            getmyad=True
        r = app_globals.mongo_adload.update({"AdvertiseId":campaign_id}, {"AdvertiseId":campaign_id, "Rynok":rynok,"GetMyAd":getmyad}, upsert=True, safe=True)
        result = {}
        for x in r:
            result[x] = str(r[x])
        print result 
        return result
    campaign_add.signature = [['struct', 'string', 'string']]
    def campaign_remove(self, campaign_id):
        ''' Убирает кампанию ``campaign_id`` из списка кампаний, которые должны рекламироваться в GetMyAd '''        
        r = app_globals.mongo_adload.remove({"AdvertiseId":campaign_id}, safe=True)
        result = {}
        for x in r:
            result[x] = str(r[x])
        print result 
    campaign_remove.signature = [['struct', 'string']]

    
    def resizedImage(self, url, width, height):
        ''' Возвращает url-адрес изображения, пережатого таким образом, чтобы вмещаться в прямоугольник
        ``height`` на ``width``. Адрес оригинального изображения передаётся в параметре ``url``.
        Можно передавать сразу множество адресов, в таком случае параметр ``url`` должен быть
        списком строк. '''
        
        cursor = app_globals.connection_rynok.cursor()
        cursor.execute('select filename from Images where url=%s and width=%s and height=%s',
                       (url, width, height))
        row = cursor.fetchone()
        if not row:
            return ""
        return 'http://rynok.yottos.ru/img/' + row['filename']
    resizedImage.signature = [['string', 'string', 'int', 'int'],
                              ['string', 'array', 'int', 'int']]
    
    def hello_world(self):
        """ Prints famous message """
        return "Hello world!"
    
    def addClick(self, offer_id, ip, click_datetime=None):
        ''' Запись перехода на рекламное предложение ``offer_id`` с адреса
            ``ip`.
            
            ``click_datetime``
                Дата и время, за которую будет записан клик. По умолчнию
                принимается за текущее время. Если передаётся, то должно
                быть сторокой в ISO формате (YYYY-MM-DDTHH:MM:SS[.mmmmmm]).
        '''
        try:
            uuid.UUID(offer_id)
        except ValueError, ex:
            return {'ok': False, 'error': 'offer_id should be uuid string!'}

        try:
            dt = dateutil.parser.parse(click_datetime)
        except (ValueError, AttributeError):
            dt = datetime.datetime.now()
        
        try:        
            cursor = app_globals.connection_adload.cursor()
            
            # Ищем в частных предложениях    
            cursor.execute('''
                select Auther, Title from Lot
                where LotID=%s and isAdvertising=1 and isBlock=0 and isTest=1'''%
                offer_id)
            try:
                row = cursor.fetchone()
                user_id = str(row.Auther)
                title = row.Title.decode('cp1251')
            except TypeError, KeyError:
                user_id = None
                
            # Ищем в магазинах
            if not user_id:
                rynok = app_globals.connection_rynok.cursor()
                rynok.execute('''
                    select MarketID, UserID, Title from View_AllActiveLot
                    where LotID = %s''' % offer_id)
                try:
                    row = rynok.fetchone()
                    user_id = str(row.UserID)
                    market_id = str(row.MarketID)
                    title = row.Title.decode('cp1251')
                except Exception, ex:
                    return {'ok': False, 'error': str(ex)}
            else:
                market_id = None
                
            assert user_id is not None
            
            # Записываем переход
            if market_id:
                cursor.execute('''exec ViewStatisticAdd @LotID=%s, @locid=0, @Host=%s, @MarketID=%s, @viewUserID=%s, @Title=%s, @Referrer='', @DateView=%s '''%
                                (offer_id, ip, market_id, user_id, title, dt) )
            else:
                cursor.execute('''exec ViewStatisticAdd @LotID=%s, @locid=0, @Host=%s, @viewUserID=%s, @Title=%s, @Referrer='', @DateView=%s '''%
                                (offer_id, ip, user_id, title, dt) )
            return {'ok': True}
        
        except Exception, ex:
            return {'ok': False, 'error': str(ex)}
