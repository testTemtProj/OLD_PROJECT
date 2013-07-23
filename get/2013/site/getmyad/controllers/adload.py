# encoding: utf-8
import logging
import datetime

from pylons import request, response, session, tmpl_context as c, url, \
    app_globals
from pylons.controllers.util import abort, redirect
from getmyad.lib.base import BaseController, render
from getmyad.lib import helpers as h
from getmyad.model.Campaign import Campaign
from getmyad.model.Offer import Offer
from getmyad import model
from uuid import uuid1
from routes.util import url_for
from pymongo import DESCENDING, ASCENDING
from urlfetch import get
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



class AdloadController(BaseController):
    
    def __before__(self, action, **params):
        user = session.get('adload_user')
        if user:
            self.user = user
            request.environ['CURRENT_USER'] = user
        else:
            self.user = ''

    
    def index(self):
        # TODO: Сделать главную страницу AdLoad 
        return ''' <html>
            <body>
              <div>
                <form action="/adload/checkPassword" method="post" id="login_form" name="login_form">
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
            session['adload_user'] = login
            session.save()
            request.environ['CURRENT_USER'] = login
        except:
            raise
            return self.index()   
        return '''
        <html>
        <body>
            <a href="/adload/adload_campaign_list">Список всех рекламных кампаний</a> |
            <a href="/adload/categories_settings">Управление тематическими категориями</a> |
<!--        <a href="/adload/campaign_update_all">Обновить все кампании</a> | -->
            <a href="/manager/checkInformers/UA" target="_blank">Проверка работы информеров</a> |
            <a href="/adload/currency_cost" target="_blank">Курс доллара</a> |
            <a href="/adload/offer_rating" target="_blank">Рейтинг Рекламных Предложений</a> |
            <a href="/adload/social" target="_blank">Соц статистика</a>

        </body>
        </html>
         '''     

    @current_user_check
    def currency_cost(self):
        ''' Страница редактирования курса доллара для пересчёта цен из AdLoad. '''
        c.dollar_cost = app_globals.adload_rpc.currencyCost('$')
        return render('/adload/currency_cost.mako.html')

    @current_user_check
    def save_currency_cost(self):
        ''' Сохранение курса доллара Adload.

            ``dollar_cost``
                POST-параметр, курс доллара.
        '''
        try:
            dollar_cost = float(request.params['dollar_cost'])
        except (KeyError, ValueError):
            return u'Неверный формат курса'
        now = datetime.datetime.now()
        app_globals.adload_rpc.setCurrencyCost('$', dollar_cost)
        return h.redirect(url_for(controller="adload", action="currency_cost"))
            
         
    @current_user_check
    def categories_settings(self):
        ''' Отображает страницу с настройками категорий предложений '''
        c.categories = self.categories()
        return render("/adload/categories.mako.html")
    
    @current_user_check
    def offer_rating(self):
        ''' Отображает страницу с рейтингом предложений '''
        return render("/adload/offer_rating.mako.html")

    @current_user_check
    def social(self):
        ''' Отображает страницу с рейтингом предложений '''
        return render("/adload/social.mako.html")

    def categories(self):
        ''' Возвращает данные для js таблицы категорий товаров'''
        categories = [(x['title'], x['clickCost'], x['guid']) for x in app_globals.db.advertise.category.find()]
        userdata = {'title': '', 'clickCost': '', 'guid': ''}
        return h.jgridDataWrapper(categories, userdata)

    
    @current_user_check
    def delCategory(self):
        ''' Удаление категории'''
        try:
            guid = request.params.get('guid')
            app_globals.db.advertise.category.remove({'guid': guid})
            return h.JSON({'error': False})
        except:
            return h.JSON({'error': True})    
    
    @current_user_check
    def saveCategory(self):
        ''' Сохранение категории'''
        try:
            clickCost = request.params.get('clickCost')
            title = request.params.get('title')
            guid = request.params.get('guid')
            if not guid:
                guid = str(uuid1()).upper()
            app_globals.db.advertise.category.update({'guid': guid}, {'$set': {'clickCost': clickCost, 'title': title}}, upsert=True)
            return h.JSON({'error': False})
        except:
            return h.JSON({'error': True})
    
        
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
        c.categories = showCondition.categories
        c.UnicImpressionLot = showCondition.UnicImpressionLot
        c.contextOnly = showCondition.contextOnly
        c.retargeting = showCondition.retargeting
        return render("/adload/campaign_settings.mako.html")

    def _campaign_settings_redirect(self):
        return h.redirect(url_for(controller="adload", action="campaign_settings", id=c.campaign_id))
    
    def keywords_settings(self, id):
        ''' Настройки кампании. ID кампании передаётся в параметре ``id`` '''
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        if not Campaign(id).exists():
            return h.JSON({"error": True, "msg": "Кампания с заданным id не существует"})       # TODO: Ошибку на нормальной странице
        token = str(uuid1()).upper()
        session[token] = {'user': session.get('user'), 'campaign_id': id}
        session.save()
        c.token = token
        offer_categoryes = {}
        for item in app_globals.db.offer.categories.find():
            offer_categoryes[item['guid']] = item['name']
        offers = app_globals.db.offer.find({'campaignId': id})
        data = []
        for offer in offers:
            data.append((offer.get('guid', ''),
                         offer.get('url',''),
                         '<a href="'+offer.get('url','')+'" target="_blank" >'+ offer.get('title', '') + '</a>',
                         offer_categoryes.get(offer.get('category', ''),''),
                         ",".join(offer.get('keywords', '')),
                         ",".join(offer.get('phrases', '')),
                         ",".join(offer.get('exactly_phrases', '')),
                         ",".join(offer.get('minus_words', ''))))
        c.offers_keywords_data = h.jqGridLocalData(data, ['id', 'url', 'title', 'category', 'keywords', 'phrases', 'exactly_phrases', 'minus_words'])
        c.offer_categoryes = offer_categoryes
        c.campaignId = id
        return render("/adload/keywords_settings.mako.html")

    def getHtml(self):
        try:
            url = request.params.get('url', None)
            if url != None:
                url = url.encode('utf-8')
                r = get(url, max_redirects=10)
                return r.body
            else:
                return '<html><body></body></html>'
        except:
            return '<html><body></body></html>'

    def keywords_save(self, id):
        oper = request.params.get('oper', False)
        guid = request.params.get('id', '')
        category = request.params.get('category', '')
        keywords = request.params.get('keywords')
        phrases = request.params.get('phrases')
        exactly_phrases = request.params.get('exactly_phrases')
        minus_words = request.params.get('minus_words')
        if keywords:
            keywords = keywords.replace('\r', ',').replace('\n', ',').replace('\t', ',').strip().split(',')
            keywords = filter(lambda x: x != '', keywords)
        else:
            keywords = []

        if minus_words:
            minus_words = minus_words.replace('\r', ',').replace('\n', ',').replace('\t', ',').strip().split(',')
            minus_words = filter(lambda x: x != '', minus_words)
        else:
            minus_words = []
        if phrases:
            phrases = phrases.replace('\r', ',').replace('\n', ',').replace('\t', ',').strip().split(',')
            phrases = filter(lambda x: x != '', phrases)
        else:
            phrases = []
        if exactly_phrases:
            exactly_phrases = exactly_phrases.replace('\r', ',').replace('\n', ',').replace('\t', ',').strip().split(',')
            exactly_phrases = filter(lambda x: x != '', exactly_phrases)
        else:
            exactly_phrases = []
        if oper:
            app_globals.db.offer.update({'guid': guid},
                                                 {'$set': {'category':category,
                                                  'keywords': keywords,
                                                  'phrases': phrases,
                                                  'exactly_phrases': exactly_phrases,
                                                  'minus_words': minus_words}}, False)
            model.mq.MQ().offer_add(guid, id)


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
        UnicImpressionLot = request.params.get('UnicImpressionLot')
        if UnicImpressionLot.isdigit():
            UnicImpressionLot = int(UnicImpressionLot)
        else:
            UnicImpressionLot = 1
        showCondition.UnicImpressionLot = UnicImpressionLot
        showCondition.contextOnly = True if request.params.get('contextOnly') else False
        showCondition.retargeting = True if request.params.get('retargeting') else False
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
#        showActiveOrAll = request.params.get("showActiveOrAll")
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
    def adload_campaign_list(self):
        '''Возвращает список всех кампаний, запущенных в AdLoad'''
        c.campaigns = app_globals.adload_rpc.campaigns_list()
        return render('/adload/campaign_list.mako.html')
 

#   @current_user_check
    def campaign_addToGetmyad(self, id):
        ''' Разрешает кампании рекламироваться в GetMyAd '''
        app_globals.adload_rpc.campaign.addToGetmyad(id)
        return redirect(url_for(controller="adload", action="campaign_overview", id=id))

    def campaign_removeFromGetmyad(self, id):
        ''' Запрещает кампании рекламироваться в GetMyAd '''
        if Campaign(id).exists():
            session['message'] = 'Сначала остановите кампанию в GetMyAd!'
            session.save()
            return redirect(url_for(controller="adload", action="campaign_overview", id=id))
        result = app_globals.adload_rpc.campaign.removeFromGetmyad(id)
        session['message'] = result.get('warning', '')
        session.save()
        return redirect(url_for(controller="adload", action="campaign_overview", id=id))
 
    def campaign_start(self, id):
        '''Запуск кампании ``id`` в GetMyAd.'''
        try:
            result = app_globals.getmyad_rpc.campaign.start(id)
        except Exception as ex:
            result = u'Неизвестная ошибка: %s' % ex
        session['message'] = u"Ответ GetMyAd: %s" % result
        session.save()
        return redirect(url_for(controller="adload", action="campaign_overview", id=id))
        
#    @current_user_check    
    def campaign_stop(self, id):
        '''Остановка кампании ``id`` в GetMyAd. '''
        try:
            result = app_globals.getmyad_rpc.campaign.stop(id)
        except Exception as ex:
            result = u'Неизвестная ошибка: %s' % ex
        session['message'] = u"Ответ GetMyAd: %s" % result
        session.save() 
        return redirect(url_for(controller="adload", action="campaign_overview", id=id))

#    @current_user_check
    def campaign_update(self, id):
        '''Обновление кампании ``id`` в GetMyAd.'''
        try:
            result = app_globals.getmyad_rpc.campaign.update(id)
        except Exception as ex:
            result = u'Неизвестная ошибка: %s' % ex
        session['message'] = u"Ответ GetMyAd: %s" % result 
        session.save()
        return redirect(url_for(controller="adload", action="campaign_overview", id=id))
    
    def campaign_update_all(self):
        '''Обновление всех запущенных в GetMyAd кампаний'''
        try:
            campaigns = app_globals.getmyad_rpc.campaign_list()
        except:
            return "Ошибка получения списка кампаний GetMyAd"
        
        result = ''
        for campaign in campaigns:
            try:
                id = campaign['id']
                msg = app_globals.getmyad_rpc.campaign.update(id)
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
        campaign = app_globals.adload_rpc.campaign.details(id)
        if not campaign:
            abort(404, comment='Кампания не найдена')
        c.campaign = campaign
        c.getmyad_details = app_globals.getmyad_rpc.campaign.details(id)
        
        if 'message' in session:
            c.message = session.get("message")
            del session["message"]
            session.save()
        else:
            c.message = ''
        return render('/adload/campaign_overview.mako.html')


 
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
        self.showCoverage = 'allowed'
        self.UnicImpressionLot = 1
        self.contextOnly = False
        self.retargeting = False
        
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

        self.UnicImpressionLot = cond.get('UnicImpressionLot', 1)
    
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
                         'showCoverage': self.showCoverage,
                         'allowed': self.allowed,
                         'ignored': self.ignored,
                         'UnicImpressionLot': self.UnicImpressionLot,
                         'retargeting': self.retargeting,
                         'contextOnly': self.contextOnly
                         }
        
        app_globals.db.campaign.update({'guid': self.campaign_id},
                                       {'$set': {'showConditions': showCondition}})
