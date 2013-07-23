# encoding: utf-8
import logging
import datetime
import time
from webhelpers.html.tags import file
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals, config
from pylons.controllers.util import abort, redirect
from getmyad.lib.base import BaseController, render
from getmyad.lib import helpers as h
from getmyad.model.Campaign import Campaign
from getmyad.model.Banner import Banner
from getmyad import model
from uuid import uuid1
from routes.util import url_for
from pymongo import DESCENDING, ASCENDING
from amqplib import client_0_8 as amqp
from getmyad.lib.base import render
from getmyad.model import mq
from pylons.controllers import XMLRPCController
from pylons.controllers.util import abort, redirect
import Image
import StringIO
import ftplib
import urllib
 
log = logging.getLogger(__name__)

def current_user_check(f):
    ''' Декоратор. Проверка есть ли в сессии авторизованный пользователь'''
    def wrapper(*args):
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        c.manager_login = user
        return f(*args)
    return wrapper


def expandtoken(f):
    ''' Декоратор находит данные сессии по токену, переданному в параметре ``token`` и 
        записывает их в ``c.info`` '''
    def wrapper(*args):
        try:
            token = request.params.get('token')
            c.info = session.get(token)
        except:
            return h.JSON({"error": True, 'msg': u"Ошибка, вы вышли из аккаунта!"})                    # TODO: Ошибку на нормальной странице     
        return f(*args)
    return wrapper

def authcheck(f):
    ''' Декоратор сравнивает текущего пользователя и пользователя, от которого пришёл запрос. ''' 
    def wrapper(*args):
        try:
            c.campaign_id = c.info['campaign_id']
            if c.info['user'] != session.get('user'): raise
        except NameError:
            return h.JSON({"error": True, 'msg':"Не задана переменная info во время вызова authcheck"})
        except:
            return h.JSON({"error": True, 'msg': u"Ошибка, вы вышли из аккаунта!"})                    # TODO: Ошибку на нормальной странице
        return f(*args)
    return wrapper 



class BannerController(BaseController):
    
    def __before__(self, action, **params):
        user = session.get('banner_user')
        if user:
            self.user = user
            request.environ['CURRENT_USER'] = user
        else:
            self.user = ''

    
    def index(self):
        return ''' <html>
            <body>
              <div>
                <form action="/banner/checkPassword" method="post" id="login_form" name="login_form">
                  <table>
                    <tr>
                      <td><b/><label for="login">Логин</label></td>
                      <td><input id="login" name="login"/></td>
                    </tr>        
                    <tr>
                      <td><b/><label for="password">Пароль</label></td>
                      <td><input type="password" id="password" name="password"/></td>
                    </tr>  
                    <tr>
                      <td><input type="submit" value="Вход" id="enter" name="enter"/></td>
                    </tr>
                  </table>  
                </form>
              </div>
            </body>
            </html>
            ''' 

    def checkPassword(self):
        ''' Проверка пароля и пользователя'''
        try:
            login = request.params.get('login')
            password = request.params.get('password')
            if not (login == 'yottos') or not (password == '123123'):
                return self.index()                 
            session['banner_user'] = login
            session.save()
            request.environ['CURRENT_USER'] = login
        except:
            raise
            return self.index()   
        return '''
        <html>
        <body>
            <a href="/banner/list_campaign" target="_blank">Банерные компании</a>  |  
            <a href="/banner/list_banner" target="_blank">Банеры</a>
        </body>
        </html>
         '''     
        
    def campaign_settings(self, id):
        ''' Настройки кампании. ID кампании передаётся в параметре ``id`` '''
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        if not Campaign(id).exists():
            return h.JSON({"error": True, "msg": "Кампания с заданным id не существует"})       # TODO: Ошибку на нормальной странице
        c.campaign = Campaign(id)
        c.campaign.load()
        
        token = str(uuid1()).upper()
        session[token] = {'user': session.get('user'), 'campaign_id': id}
        session.save()
        c.token = token  
        
        if session.get('showActiveOrAll'):
            c.showActiveOrAll = session.get('showActiveOrAll')
        else:    
            c.showActiveOrAll = "all"
        c.common = self.commonList(id)
        structuredShowCondition = self.structuredShowCondition(id)
        c.shown = structuredShowCondition.get('allowed')
        c.ignored = structuredShowCondition.get('ignored')
        
        showCondition = ShowCondition(id)
        showCondition.load()
        c.days = showCondition.daysOfWeek
        c.startShowTimeHours = showCondition.startShowTimeHours
        c.startShowTimeMinutes = showCondition.startShowTimeMinutes
        c.endShowTimeHours = showCondition.endShowTimeHours
        c.endShowTimeMinutes = showCondition.endShowTimeMinutes
        c.clicksPerDayLimit = showCondition.clicksPerDayLimit
        c.showCoverage = showCondition.showCoverage
        c.geoTargeting = showCondition.geoTargeting
        c.regionTargeting = showCondition.regionTargeting
        c.all_geo_countries = [x for x in app_globals.db.geo.country.find().sort('ru')]
        c.all_geo_regions = [(x['region'], x.get('ru')) for x in app_globals.db.geo.regions.find().sort('ru')]
        c.all_categories = [{'title':x['title'], 'guid': x['guid']} for x in app_globals.db.advertise.category.find().sort('title')]
        c.all_topic = [{'title':x['title'], 'guid': x['guid']} for x in app_globals.db.topic.find().sort('title')]
        c.categories = showCondition.categories
        c.topic = showCondition.topic
        c.UnicImpressionLot = showCondition.UnicImpressionLot
        return render("/banner/campaign_settings.mako.html")

    def _campaign_settings_redirect(self):
        return h.redirect(url_for(controller="banner", action="campaign_settings", id=c.campaign_id))
    

    @expandtoken    
    @authcheck
    def saveConditions(self):
        ''' Сохранение настроек кампании.'''
        showCondition = ShowCondition(c.campaign_id)
        showCondition.load()
        showCondition.startShowTimeHours = request.params.get('hours_from')
        showCondition.startShowTimeMinutes = request.params.get('minutes_from')
        showCondition.endShowTimeHours = request.params.get('hours_to')
        showCondition.endShowTimeMinutes = request.params.get('minutes_to')
        showCondition.clicksPerDayLimit = request.params.get('clicksPerDayLimit')
        showCondition.showCoverage = request.params.get('showCoverage', 'allowed')
        showCondition.daysOfWeek = []
        for i in range(7):
            if request.params.get('day' + str(i + 1)):
                showCondition.daysOfWeek.append(i + 1)

        geotargeting_params = request.params.getall('geoTargeting')
        geotargeting = filter(lambda x: len(x) == 2, geotargeting_params)
        other_countries = filter(lambda x: len(x) > 2, geotargeting_params)
        for country in other_countries:
            tempo = app_globals.db.geo.country.find_one({'name': country})
            if tempo:
                geotargeting.extend(tempo['country'])

        showCondition.geoTargeting = geotargeting

        showCondition.regionTargeting = request.params.getall('regionTargeting')
        showCondition.categories = request.params.getall('all_categories')
        showCondition.topic = request.params.getall('all_topic')
        UnicImpressionLot = request.params.get('UnicImpressionLot')
        if UnicImpressionLot.isdigit():
            UnicImpressionLot = int(UnicImpressionLot)
        else:
            UnicImpressionLot = -1
        showCondition.UnicImpressionLot = UnicImpressionLot
        showCondition.save()
        campaign = Campaign(c.campaign_id)
        campaign.load()
        campaign.social = True if request.params.get('socialCampaign') else False
        campaign.yottos_partner_marker = True if request.params.get('yottosPartnerMarker') else False
        campaign.yottos_attractor_marker = True if request.params.get('yottosAttractorMarker') else False
        campaign.save()
        model.mq.MQ().campaign_update(c.campaign_id)
        return self._campaign_settings_redirect()
    
    
    def commonList(self, campaign_id):
        ''' Возвращает все активные аккаунты, домены и информеры, которые не относятся ни
        к игнорируемым, ни к разрешённым в кампании ``campaign_id``.
        
        Возвращаемая структура имеет следующий вид::
        
            accounts: ['a1': 'green', 'a2': 'grey', 'a3'],
            domains: {'a3': ['d1', 'd2', 'd3'],
                      'a4': ['d4', 'd5', 'd6']},
            adv: {'a3': {'d1': [{'title':'adv1', 'guid': '--'}, {'title':'adv2', 'guid': '--'}],
                         'd2': [{'title':'adv3', 'guid': '--'}, {'title':'adv4', 'guid': '--'}]},
                  'a4': {'d5': [{'title':'adv5', 'guid': '--'}, {'title':'adv6', 'guid': '--'}]}
                   }          
                      
            }
        '''
        showCondition = ShowCondition(campaign_id)
        showCondition.load()
       
#        all_accounts = [x['login'] for x in app_globals.db.users.find().sort('login')]
        try:    
            if c.showActiveOrAll == 'active':
                all_accounts = [x['user'] for x in app_globals.db.stats_user_summary.find({'activity': {'$ne': 'orangeflag'}}).sort('user')]
            else:    
                all_accounts = [x['user'] for x in app_globals.db.stats_user_summary.find({}).sort('user')]
        except:
            all_accounts = [x['user'] for x in app_globals.db.stats_user_summary.find({}).sort('user')]
            c.showActiveOrAll = "all"        
        accounts = []
        for x in all_accounts:
            if x not in showCondition.allowed_accounts:
                if x not in showCondition.ignored_accounts:
                    accounts.append(x)
        
        domains = {}
        for user_domain in app_globals.db.domain.find({'login': {'$in': all_accounts}}) or []:
            for key,value in user_domain['domains'].items(): 
                if value not in showCondition.allowed_domains:
                    if value not in showCondition.ignored_domains:
                        if not domains.get(user_domain['login']):
                            domains[user_domain['login']] = []
                        domains[user_domain['login']].append(value)
            
    
        adv = {}
        for advertise in app_globals.db.informer.find(
                {'user': {'$in': all_accounts}},
                ['user', 'title', 'guid', 'domain']):
            account = advertise['user']
            title = advertise['title']
            guid = advertise['guid']
            domain = advertise.get('domain', '')
            if guid not in showCondition.allowed_informers:
                if guid not in showCondition.ignored_informers:
                    if not adv.get(account):
                        adv[account] = {}
                    if not adv[account].get(domain):
                        adv[account][domain] = []
                    adv[account][domain].append({'title': title, 'guid': guid})     
        
        return {'accounts': accounts, 'domains': domains, 'adv': adv}

    def structuredShowCondition(self, campaign_id):
        '''  Возвращает разрешённые и запрещённые аккаунты, домены, информеры.
        
        Возвращает структуру вида::
        
            {ignored:
                    {accounts: ['a1', 'a2', 'a3'],
                     domains: {'a3': ['d1', 'd2', 'd3'],
                               'a4': ['d4', 'd5', 'd6']},
                     adv: {'a3': {'d1': [{'title':'adv1', 'guid': '--'}, {'title':'adv2', 'guid': '--'}],
                                  'd2': [{'title':'adv3', 'guid': '--'}, {'title':'adv4', 'guid': '--'}]},
                           'a4': {'d5': [{'title':'adv5', 'guid': '--'}, {'title':'adv6', 'guid': '--'}]}
                            }
                               
                     },
             allowed: ......        
             }
             
        '''

        list = {}
        list['allowed'] = {}
        list['ignored'] = {}
        showCondition = ShowCondition(campaign_id)
        showCondition.load()
            
        # accounts   
        list['allowed']['accounts'] = showCondition.allowed_accounts
        list['ignored']['accounts'] = showCondition.ignored_accounts
        # domains
        list['allowed']['domains'] = {}
        list['ignored']['domains'] = {}
        for allowed_domain in showCondition.allowed_domains:
            for user_domain in app_globals.db.domain.find({}):
                for item in user_domain['domains']:
                    d = user_domain['domains'][item]
                    if d in allowed_domain:
                        if not list['allowed']['domains'].get(user_domain['login']):
                                list['allowed']['domains'][user_domain['login']] = []
                        list['allowed']['domains'][user_domain['login']].append(allowed_domain)

        for ignored_domain in showCondition.ignored_domains:
            for user_domain in app_globals.db.domain.find({}):
                for item in user_domain['domains']:
                    d = user_domain['domains'][item]
                    if d in ignored_domain:
                        if not list['ignored']['domains'].get(user_domain['login']):
                                list['ignored']['domains'][user_domain['login']] = []
                        list['ignored']['domains'][user_domain['login']].append(ignored_domain)            
  
        # advertises
        list['allowed']['adv'] = {}
        list['ignored']['adv'] = {}
        for allowed_adv in showCondition.allowed_informers:
            adv = app_globals.db.informer.find_one(
                {'guid': allowed_adv},
                ['user', 'domain', 'title', 'guid'])
            account = adv['user']
            domain = adv['domain']
            title = adv['title']
            guid = adv['guid']
            if not list['allowed']['adv'].get(account):
                list['allowed']['adv'][account] = {}
            if not list['allowed']['adv'][account].get(domain):
                list['allowed']['adv'][account][domain] = []
            list['allowed']['adv'][account][domain].append({'title': title, 'guid': guid})
        
        for ignored_adv in showCondition.ignored_informers:
            adv = app_globals.db.informer.find_one(
                {'guid': ignored_adv},
                ['user', 'domain', 'title', 'guid'])
            account = adv['user']
            domain = adv['domain']
            title = adv['title']
            guid = adv['guid']
            if not list['ignored']['adv'].get(account):
                list['ignored']['adv'][account] = {}
            if not list['ignored']['adv'][account].get(domain):
                list['ignored']['adv'][account][domain] = []
            list['ignored']['adv'][account][domain].append({'title': title, 'guid': guid})    
        return {'allowed': list['allowed'], 'ignored': list['ignored']}
    
    
    @expandtoken    
    @authcheck 
    def switchShowActiveOrAll(self):
        session['showActiveOrAll'] = request.params.get("showActiveOrAll")
        session.save()
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck    
    def addAccountsToShowList(self):
        ''' Добавление аккаунтов в список отображаемых'''
        try:
            accounts = request.params.getall('common-accounts-list')
            for account in accounts:
                app_globals.db.campaign.update({'guid': c.campaign_id},
                                               {'$addToSet': {'showConditions.allowed.accounts': account} }, safe=True, upsert=True)
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
            
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def addAccountsToIgnoreList(self):
        ''' Добавление аккаунтов в список игнорируемых'''
        try:
            accounts = request.params.getall('common-accounts-list')
            for account in accounts:
                app_globals.db.campaign.update({'guid': c.campaign_id},
                                               {'$addToSet': {'showConditions.ignored.accounts': account} }, safe=True, upsert=True)
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def addDomainsToShowList(self):
        ''' Добавление доменов в список отображаемых'''
        try:
            domains = request.params.getall('common-domains-list')
            for domain in domains:
                app_globals.db.campaign.update({'guid': c.campaign_id},
                                               {'$addToSet': {'showConditions.allowed.domains': domain} }, safe=True, upsert=True)
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')      
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def addDomainsToIgnoreList(self):
        ''' Добавление доменов в список игнорируемых'''
        try:
            domains = request.params.getall('common-domains-list')
            for domain in domains:
                app_globals.db.campaign.update({'guid': c.campaign_id},
                                               {'$addToSet': {'showConditions.ignored.domains': domain} }, safe=True, upsert=True)
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck    
    def addAdvToShowList(self):
        ''' Добавление информеров в список отображаемых'''
        try:
            advs = request.params.getall('common-adv-list')
            for adv in advs:
                app_globals.db.campaign.update({'guid': c.campaign_id},
                                               {'$addToSet': {'showConditions.allowed.informers': adv} }, safe=True, upsert=True)
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')        
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def addAdvToIgnoreList(self):
        ''' Добавление информеров в список игнорируемых'''
        try:
            advs = request.params.getall('common-adv-list')
            for adv in advs:
                app_globals.db.campaign.update({'guid': c.campaign_id},
                                               {'$addToSet': {'showConditions.ignored.informers': adv} }, safe=True, upsert=True)
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error') 
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def removeAccountsFromShowList(self):
        ''' Убирание аккаунтов из списка отображаемых '''
        try:
            accounts = request.params.getall('show-accounts-list')
            app_globals.db.campaign.update({'guid': c.campaign_id},
                                           {'$pullAll': {'showConditions.allowed.accounts': accounts}})
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')    
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def removeDomainsFromShowList(self):
        ''' Убирание доменов из списка отображаемых '''
        try:
            domains = request.params.getall('show-domains-list')
            app_globals.db.campaign.update({'guid': c.campaign_id},
                                           {'$pullAll': {'showConditions.allowed.domains': domains}})
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def removeAdvFromShowList(self):
        ''' Убирание информера из списка отображаемых'''
        try:
            advs = request.params.getall('show-adv-list')
            app_globals.db.campaign.update({'guid': c.campaign_id},
                                           {'$pullAll': {'showConditions.allowed.informers': advs}})
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def removeAccountsFromIgnoreList(self):
        ''' Убирание аккаунта из списка игнорируемых'''
        try:
            accounts = request.params.getall('ignore-accounts-list')
            app_globals.db.campaign.update({'guid': c.campaign_id},
                                           {'$pullAll': {'showConditions.ignored.accounts': accounts}})
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def removeDomainsFromIgnoreList(self):
        ''' Убирание доменов из списка игнорируемых'''
        try:
            domains = request.params.getall('ignore-domains-list')
            app_globals.db.campaign.update({'guid': c.campaign_id},
                                           {'$pullAll': {'showConditions.ignored.domains': domains}})
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
        return self._campaign_settings_redirect()
    
    @expandtoken    
    @authcheck
    def removeAdvFromIgnoreList(self):
        ''' Убирание информеров из списка игнорируемых'''
        try:
            advs = request.params.getall('ignore-adv-list')
            app_globals.db.campaign.update({'guid': c.campaign_id},
                                           {'$pullAll': {'showConditions.ignored.informers': advs}})
            model.mq.MQ().campaign_update(c.campaign_id)
        except:
            log.debug('error')
        return self._campaign_settings_redirect()
 
    @current_user_check
    def list_campaign(self):
        camp = app_globals.db.banner.campaign.find()
        c.campaigns = []
        for item in camp:
            id = item.get('guid', '')
            status = app_globals.getmyad_banner_rpc.campaign.details(id).get('status','not_found')
            title = item.get('title', '')
            c.campaigns.append({'id':id, 'title':title, 'status':status})
        return render('/banner/campaign_list.mako.html')

    def list_banner(self):
        banner = app_globals.db.banner.offer.find()
        camp = app_globals.db.banner.campaign.find()
        c.banner = []
        c.campaigns = []
        for item in banner:
            item['status'] = app_globals.getmyad_banner_rpc.campaign.details(item['campaignId']).get('status','not_found')
            c.banner.append(item)
        for item in camp:
            id = item.get('guid', '')
            title = item.get('title', '')
            c.campaigns.append({'id':id, 'title':title})
        return render('/banner/banner_list.mako.html')
 
    def createCampaign(self):
        id = str(uuid1()).lower()
        title = request.POST['name']
        app_globals.db.banner.campaign.insert({'guid':id, 'title':title})
        return redirect(url(controller="banner", action="campaign_overview", id=id))
    def banner_false(self):
        c.message = 'Неправильный файл картинки баннера. Баннер не удалось создать!'
        return render('/banner/banner_false.mako.html')

    def createBanner(self):
        id = str(uuid1()).lower()
        try:
            banner_size = request.POST['banner_size'].encode('utf-8').split('x')
            offer = Banner(id)
            print banner_size
            offer.title = request.POST['name']
            offer.imp_cost = request.POST['imp_cost']
            offer.budget = request.POST['budget']
            offer.url = request.POST['url']
            if bool(request.POST.get('flash',False)):
                flash = self.upload_flash(request.params.get('myfile',''))
                offer.swf = flash
            else:
                img = self.resize_and_upload_image(request.params.get('myfile',''), int(banner_size[1]), int(banner_size[0]))
                if len(img) == 0:
                    print 'image not valid'
                    return redirect(url(controller="banner", action="banner_false"))
                offer.image = img
            offer.date_added = datetime.datetime.now()
            offer.campaign = request.POST['camp_list']
            offer.type = 'banner'
            offer.width =  banner_size[0]
            offer.height =  banner_size[1]
            offer.save()
        except Exception as ex:
            print ex
            return redirect(url(controller="banner", action="banner_false"))
        return redirect(url(controller="banner", action="list_banner"))

    def updateBanner(self, id):
        offer = Banner(id)
        offer.title = request.POST['name']
        offer.imp_cost = request.POST['imp_cost']
        offer.budget = request.POST['budget']
        offer.url = request.POST['url']
        offer.campaign = request.POST['camp_list']
        offer.update()
        return redirect(url(controller="banner", action="banner_overview", id=id))
 
    def updateBannerBudget(self, id):
        idi = request.POST['bann_list']
        budget = float(request.POST['budget'])
        if id != idi:
            offer = Banner(id)
            offer.load()
            print offer.budget, budget
            if offer.budget >= budget:
                offeri = Banner(idi)
                offeri.load()
                app_globals.db.banner.offer.update({'guid': offer.id},{'$set': {'budget':float(offer.budget - budget)}})
                app_globals.db.banner.offer.update({'guid': offeri.id},{'$set': {'budget':float(offeri.budget + budget)}})
                date = datetime.datetime.now()
                app_globals.db.banner.payment.insert({'guid': offer.id,'budget': float(- budget), 'date':date})
                app_globals.db.banner.payment.insert({'guid': offeri.id,'budget': float( budget), 'date':date})

        return redirect(url(controller="banner", action="banner_overview", id=id))

    def campaign_start(self, id):
        '''Запуск кампании ``id`` в GetMyAd.'''
        try:
            result = app_globals.getmyad_banner_rpc.campaign.start(id)
        except Exception as ex:
            result = u'Неизвестная ошибка: %s' % ex
        session['message'] = u"Ответ GetMyAd: %s" % result
        session.save()
        return redirect(url_for(controller="banner", action="campaign_overview", id=id))
        
#    @current_user_check    
    def campaign_stop(self, id):
        '''Остановка кампании ``id`` в GetMyAd. '''
        try:
            result = app_globals.getmyad_banner_rpc.campaign.stop(id)
        except Exception as ex:
            result = u'Неизвестная ошибка: %s' % ex
        session['message'] = u"Ответ GetMyAd: %s" % result
        session.save() 
        return redirect(url_for(controller="banner", action="campaign_overview", id=id))

#    @current_user_check
    def campaign_update(self, id):
        '''Обновление кампании ``id`` в GetMyAd.'''
        try:
            result = app_globals.getmyad_banner_rpc.campaign.update(id)
        except Exception as ex:
            result = u'Неизвестная ошибка: %s' % ex
        session['message'] = u"Ответ GetMyAd: %s" % result 
        session.save()
        return redirect(url_for(controller="banner", action="campaign_overview", id=id))
    
    def campaign_update_all(self):
        '''Обновление всех запущенных в GetMyAd кампаний'''
        try:
            campaigns = app_globals.getmyad_banner_rpc.campaign_list()
        except:
            return "Ошибка получения списка кампаний GetMyAd"
        
        result = ''
        for campaign in campaigns:
            try:
                id = campaign['id']
                msg = app_globals.getmyad_banner_rpc.campaign.update(id)
                log.info("Updating campaign %s: %s" % (id, msg))
            except Exception, ex:
                msg = repr(ex)
            result += '<p>Campaign %s: %s</p>' % (id, msg)
        return result
    
    def campaign_overview(self, id):
        ''' Страница обзора кампании ``id``. '''
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        if not id:
            abort(404)
        camp = app_globals.db.banner.campaign.find_one({'guid':id})
        campaign = {'id': id,
                'title': camp.get('title','')
                   }
        if not campaign:
            abort(404, comment='Кампания не найдена')
        c.campaign = campaign
        c.getmyad_details = app_globals.getmyad_banner_rpc.campaign.details(id)
        if 'message' in session:
            c.message = session.get("message")
            del session["message"]
            session.save()
        else:
            c.message = ''
        return render('/banner/campaign_overview.mako.html')
    def delete_banner(self, id):
        app_globals.db.banner.offer.remove({'guid':id})
        return redirect(url_for(controller="banner", action="list_banner"))

    def campaign_delete(self, id):
        app_globals.db.banner.campaign.remove({'guid':id})
        return redirect(url_for(controller="banner", action="list_campaign"))

    def banner_overview(self, id):
        ''' Страница обзора кампании ``id``. '''
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        if not id:
            abort(404)
        date = datetime.datetime.now()
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        banner = app_globals.db.banner.offer.find_one({'guid':id})
        reallocate = app_globals.db.banner.stats_daily.find_one({'guid':id, 'date':{'$gte':date}})
        if reallocate != None:
            c.reallocate = True
        else:
            c.reallocate = False
        if not banner:
            abort(404, comment=u'Баннер не найден')
        banner['status'] = app_globals.getmyad_banner_rpc.campaign.details(banner['campaignId']).get('status','not_found')
        camp = app_globals.db.banner.campaign.find_one({'guid': banner['campaignId']})
        if camp == None:
            campaign = {'title': u'Не присвоена'}
            campaign['campaignId'] = ''
        else:
            campaign = {'title': camp.get('title','')}
            campaign['campaignId'] = banner['campaignId']
        camp = app_globals.db.banner.campaign.find()
        bann = app_globals.db.banner.offer.find()
        c.campaigns = []
        c.banners = []
        for item in camp:
            id = item.get('guid', '')
            title = item.get('title', '')
            c.campaigns.append({'id':id, 'title':title})
        for item in bann:
            id = item.get('guid', '')
            title = item.get('title', '')
            c.banners.append({'id':id, 'title':title})
        c.campaign = campaign
        c.banner = banner
        c.message = ''
        return render('/banner/banner_overview.mako.html')

    def banner_stat(self, id):
        ''' Страница обзора кампании ``id``. '''
        date = datetime.date.today() - datetime.timedelta(days=1)
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        c.date = date.strftime("%d.%m.%Y")
        banner = app_globals.db.banner.offer.find_one({'guid':id})
        if not banner:
            abort(404, comment=u'Баннер не найден')
        c.banner = banner
        return render('/banner/banner_stat.mako.html')

    def stat(self, id):
        ''' Страница обзора кампании ``id``. '''
        data = []
        datas = []
        date = datetime.date.today() 
        date = datetime.datetime(date.year, date.month, date.day, 0, 0)
        banner = app_globals.db.banner.stats_daily.group(
                                                    key = ['date'],
                                                    condition = {'guid':id,'date':{'$lt':date}},
                                                    reduce = '''function(o, p) {
                                                    p.imp += o.banner_impressions || 0;
                                                    p.sum += o.cost || 0;
                                                    }''',
                                                    initial = {'sum':0,'imp':0}
                                                     )
        for item in banner:
            data.append((time.mktime(item['date'].timetuple()),
                         item['imp'],
                         h.formatMoney(item['sum'])
                        ))  
        data.sort(key=lambda x: x[0], reverse = False)
        for item in data:
            datas.append((datetime.datetime.fromtimestamp(item[0]).strftime("%d.%m.%Y"),
                         item[1],
                         item[2]
                        ))  
        return h.jgridDataWrapper(datas, records_on_page = 20)

    def stat_pay(self, id):
        ''' Страница обзора кампании ``id``. '''
        data = []
        banner = app_globals.db.banner.payment.find({'guid':id}).sort('date')
        for item in banner:
            data.append((item['date'].strftime("%d.%m.%Y %H:%M"),
                         h.formatMoney(item['budget'])
                        ))  
        return h.jgridDataWrapper(data, records_on_page = 20)

    def resize_and_upload_image(self, req, height, width):
        ''' заливает изображение на ftp для раздачи статики.
            Возвращает url нового файла или пустую строку в случае ошибки.
        '''
        try:
            files = req.file.read()
            data = StringIO.StringIO(files)
            data.seek(0)
            buf = StringIO.StringIO()
            i = Image.open(data)
            if not config.get('cdn_server_url') or not config.get('cdn_ftp'):
                log.warning('Не заданы настройки сервера CDN. Проверьте .ini файл.')
                return ''
            size_key = '%sx%s' % (height,width)
            if (i.size[0] != width) and (i.size[1] != height):
                print i.size[0], width , i.size[1], height
                log.warning('Не правильный размер файл.')
                return ''
            if i.format == 'GIF':
                new_filename = uuid1().get_hex() + '.gif'
                ftp = ftplib.FTP(host=config.get('cdn_ftp'))
                ftp.login(config.get('cdn_ftp_user'), config.get('cdn_ftp_password'))
                ftp.cwd(config.get('cdn_ftp_path'))
                ftp.cwd('banner')
                ftp.storbinary('STOR %s' % new_filename, StringIO.StringIO(files))
                ftp.close()
                data.close()
                buf.close()
            else:
                if i.mode != 'RGB':
                    i = i.convert('RGB')
                i.save(buf, 'JPEG')
                buf.seek(0)
                new_filename = uuid1().get_hex() + '.jpg'
                ftp = ftplib.FTP(host=config.get('cdn_ftp'))
                ftp.login(config.get('cdn_ftp_user'), config.get('cdn_ftp_password'))
                ftp.cwd(config.get('cdn_ftp_path'))
                ftp.cwd('banner')
                ftp.storbinary('STOR %s' % new_filename, buf)
                ftp.close()
                data.close()
                buf.close()
            new_url = config.get('cdn_server_url') + 'banner/' + new_filename

            return new_url
        except Exception as ex:
            log.exception(ex)
            return ''
    resize_and_upload_image.signature = [['string', 'string', 'int', 'int']]

    def upload_flash(self, req):
        ''' заливает изображение на ftp для раздачи статики.
            Возвращает url нового файла или пустую строку в случае ошибки.
        '''
        try:
            files = req.file.read()
            new_filename = uuid1().get_hex() + '.swf'
            ftp = ftplib.FTP(host=config.get('cdn_ftp'))
            ftp.login(config.get('cdn_ftp_user'), config.get('cdn_ftp_password'))
            ftp.cwd(config.get('cdn_ftp_path'))
            ftp.cwd('banner')
            ftp.storbinary('STOR %s' % new_filename, StringIO.StringIO(files))
            ftp.close()
            new_url = config.get('cdn_server_url') + 'banner/' + new_filename
            return new_url
        except Exception as ex:
            log.exception(ex)
            return ''
    resize_and_upload_image.signature = [['string', 'string']]

 
class ShowCondition:
    ''' Класс для загрузки и сохранения настроек кампании  '''
    
    def __init__(self, campaign_id):
        self.campaign_id = campaign_id
        self.allowed = {}
        self.allowed_accounts = []
        self.allowed_domains = []
        self.allowed_informers = []
        self.ignored = {}
        self.ignored_accounts = []
        self.ignored_domains = []
        self.ignored_informers = []
        self.daysOfWeek = []  
        self.startShowTime = {'hours': '00', 'minutes': '00'}
        self.startShowTimeHours = self.startShowTime.get('hours')
        self.startShowTimeMinutes = self.startShowTime.get('minutes')
        self.endShowTime = {'hours': '00', 'minutes': '00'}
        self.endShowTimeHours = self.endShowTime.get('hours')
        self.endShowTimeMinutes = self.endShowTime.get('minutes')
        self.clicksPerDayLimit = 0
        self.geoTargeting = []
        self.regionTargeting = []
        self.categories = []
        self.topic = []
        self.showCoverage = 'allowed'
        self.UnicImpressionLot = -1
        
    def load(self):
        ''' Загружает из базы данных настройки кампании.
        
        Если кампания не найдена, то генерирует исключение ``Campaign.NotFoundError``.
        '''
        campaign = app_globals.db.campaign.find_one({'guid': self.campaign_id})
        if not campaign:
            raise Campaign.NotFoundError()
        
        cond = campaign.get('showConditions', {})
        self.allowed = cond.get('allowed') or {}
        self.ignored = cond.get('ignored') or {}
        self.allowed_accounts = self.allowed.get('accounts') or []
        self.allowed_domains = self.allowed.get('domains') or []
        self.allowed_informers = self.allowed.get('informers') or []
        
        self.ignored_accounts = self.ignored.get('accounts') or []
        self.ignored_domains = self.ignored.get('domains') or []
        self.ignored_informers = self.ignored.get('informers') or []
        
        self.showCoverage = cond.get("showCoverage", 'allowed')
        
        self.daysOfWeek = cond.get('daysOfWeek') or self.daysOfWeek
        self.startShowTime = cond.get('startShowTime') or self.startShowTime
        self.startShowTimeHours = self.startShowTime.get('hours') or self.startShowTimeHours
        self.startShowTimeMinutes = self.startShowTime.get('minutes') or self.startShowTimeMinutes
        self.endShowTime = cond.get('endShowTime') or self.endShowTime
        self.endShowTimeHours = self.endShowTime.get('hours') or self.endShowTimeHours
        self.endShowTimeMinutes = self.endShowTime.get('minutes') or self.endShowTimeMinutes
        
        self.clicksPerDayLimit = int(cond.get('clicksPerDayLimit') or self.clicksPerDayLimit)
        self.geoTargeting = cond.get('geoTargeting') or self.geoTargeting
        self.regionTargeting = cond.get('regionTargeting') or self.regionTargeting
        self.categories = cond.get('categories') or []
        self.topic = cond.get('topic') or []

        self.UnicImpressionLot = cond.get('UnicImpressionLot', -1)
    
    def save(self):
        ''' Сохранение настроек кампании'''
        try:
            self.clicksPerDayLimit = int(self.clicksPerDayLimit)
        except:
            self.clicksPerDayLimit = 0

        showCondition = {'clicksPerDayLimit': self.clicksPerDayLimit,
                         'startShowTime': {'hours': self.startShowTimeHours,
                                           'minutes': self.startShowTimeMinutes},
                         'endShowTime': {'hours': self.endShowTimeHours, 
                                         'minutes': self.endShowTimeMinutes},
                         'geoTargeting': self.geoTargeting,
                         'regionTargeting': self.regionTargeting,
                         'daysOfWeek': self.daysOfWeek,
                         'categories': self.categories,
                         'topic': self.topic,
                         'showCoverage': self.showCoverage,
                         'allowed': self.allowed,
                         'ignored': self.ignored,
                         'UnicImpressionLot': self.UnicImpressionLot
                         }
        
        app_globals.db.campaign.update({'guid': self.campaign_id},
                                       {'$set': {'showConditions': showCondition}})
