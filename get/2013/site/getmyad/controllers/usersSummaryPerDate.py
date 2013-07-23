# -*- coding: utf-8 -*-
import logging
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from datetime import datetime, timedelta
from getmyad import model
from getmyad.lib import helpers as h
from formencode import Schema
from getmyad.lib.base import BaseController, render
from getmyad.model import Account, AccountReports, Permission
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals
from pylons.controllers.util import abort, redirect
from routes.util import redirect_to
from datetime import datetime, date, time
import json
import logging
import bson.json_util


from getmyad.lib.base import BaseController, render

log = logging.getLogger(__name__)

class UserssummaryperdateController(BaseController):
    
    def dataUsersSummary(self):
        """Суммарные данные по всем пользователям"""
        elapsed_start_time = datetime.now()
        today = datetime.today()
        yday = today - timedelta(days=1)
        byday = today - timedelta(days=2)

        all_active_domains_today = self.active_domains(today)
        all_active_domains_yday = self.active_domains(yday)
        all_active_domains_byday = self.active_domains(byday)

        for user in self._usersList():
            login = user['login']
            s = AccountReports(Account(login)).balance()
            periodSummImp = self.accountPeriodSummImp(login)
            sToday = periodSummImp['income']['today']
            sYesterday = periodSummImp['income']['yesterday']
            sBeforeYesterday = periodSummImp['income']['before_yesterday']
            sWeek = periodSummImp['income']['week']
            sMonth = periodSummImp['income']['month']
            sYear = periodSummImp['income']['year']
            iToday = periodSummImp['impressions']['today']
            iYesterday = periodSummImp['impressions']['yesterday']
            iBeforeYesterday = periodSummImp['impressions']['before_yesterday']
            iWeek = periodSummImp['impressions']['week']
            iMonth = periodSummImp['impressions']['month']
            iYear = periodSummImp['impressions']['year']
            iToday_block = periodSummImp['impressions_block']['today']
            iYesterday_block = periodSummImp['impressions_block']['yesterday']
            iBeforeYesterday_block = periodSummImp['impressions_block']['before_yesterday']
            iWeek_block = periodSummImp['impressions_block']['week']
            iMonth_block = periodSummImp['impressions_block']['month']
            iYear_block = periodSummImp['impressions_block']['year']
            dayCTR = self.account_CTR_for_period(login, yday, today)
            weekCTR = self.account_CTR_for_period(login, today - timedelta(days=7), today)
            dayCTR_block = self.account_CTR_block_for_period(login, yday, today)
            weekCTR_block = self.account_CTR_block_for_period(login, today - timedelta(days=7), today)
            activity = self.userActivity(login, today)
            activity_yesterday = self.userActivity(login, yday)
            activity_before_yesterday = self.userActivity(login, byday)
            active_domains_today = all_active_domains_today.get(login, 0)
            active_domains_yday = all_active_domains_yday.get(login, 0)
            active_domains_byday = all_active_domains_byday.get(login, 0)
            
            app_globals.db.user.summary_per_date.update({'login': login},
                                            {'$set':
                                            {'income': 
                                                {'today': sToday,
                                                 'yesterday': sYesterday,
                                                 'before_yesterday': sBeforeYesterday,
                                                 'week': sWeek,
                                                 'month': sMonth,
                                                 'year': sYear},
                                             'impressions':
                                                 {'today': iToday,
                                                 'today_block': iToday_block,
                                                 'yesterday': iYesterday,
                                                 'yesterday_block': iYesterday_block,
                                                 'before_yesterday': iBeforeYesterday,
                                                 'before_yesterday_block': iBeforeYesterday_block,
                                                 'week': iWeek,
                                                 'week_block': iWeek_block,
                                                 'month': iMonth,
                                                 'month_block': iMonth_block,
                                                 'year': iYear,
                                                 'year_block': iYear_block},
                                             'day_CTR': dayCTR,
                                             'week_CTR': weekCTR,
                                             'day_CTR_block': dayCTR_block,
                                             'week_CTR_block': weekCTR_block,
                                             'summ': s,
                                             'activity': activity,
                                             'activity_yesterday': activity_yesterday,
                                             'activity_before_yesterday': activity_before_yesterday,
                                             'registrationDate': user['registrationDate'],
                                             'active_domains':
                                                {'today': active_domains_today,
                                                 'yesterday': active_domains_yday,
                                                 'before_yesterday': active_domains_byday}
                                            }},
                                            safe=True,
                                            upsert=True)
        current_time = datetime.today()
        app_globals.db.config.update({'key': 'last user.summary_per_date update'},
                                     {'$set': {'value': current_time}},
                                     upsert=True) 
        print 'Agregate DataUsersSummary  is end %s second' % (datetime.now() - elapsed_start_time).seconds

    def userActivity(self, user_login, date):
        ''' Возвращает флаг активности пользователя:
        
            greenflag -- пользователь активен
            orangeflag -- пользователь неактивен
            redflag -- пользователь переходи из активного в неактивные.
            
            Пользователь считается активным, если в сутки был совершён хотя бы один клик или
            более 100 показов. 

            Параметр date - это день за который надо определить активность.'''
        advertises = [x['guid']
                      for x in app_globals.db.informer.find({'user': user_login}, ['guid'])]
        d = date
        today = datetime(d.year, d.month, d.day)
        yesterday = today - timedelta(days=1)
        before_yesterday = today - timedelta(days=2)
        dateStart = before_yesterday
        dateEnd = today
        data = model.StatisticReport().statUserGroupedByDate(user_login, dateStart=before_yesterday, dateEnd=today)
        if not data:
            return 'orangeflag'
        by = False  # before yesterday
        y = False   # yesterday
        t = False   # today
        c = False   # clicks count
        for x in data:
            if x['date'] == before_yesterday:
                if x['impressions'] > 100 or x['unique'] > 0:
                    by = True
            elif x['date'] == today:
                if x['impressions'] > 100 or x['unique'] > 0:
                    t = True
            elif x['date'] == yesterday:
                if x['impressions'] > 100 or x['unique'] > 0:
                    y = True
            if x['unique'] > 0:
                c = True

        if t:
            act = "greenflag"
        elif not by and not y and not t:
            act = "orangeflag"
        else:
            act = "redflag"
            
        return act


    def active_domains(self, date):
        ''' Возвращает данные об активности доменов пользователей по состоянию
            на дату ``date``::

                {'login1': 3,    // у пользователя login1 3 активных домена
                 'login2': 1,
                 // ...
                }

            Критерий активности домена: один клик или не менее 100 показов.
        '''
        db = app_globals.db
        date = h.trim_time(date)

        informer_info = {}
        for x in db.informer.find():
            informer_info[x.get('guid')] = {'domain' : x.get('domain'),
                                            'user': x.get('user')}

        domain_data = {}
        for x in app_globals.db.stats_daily_adv.find({'date': date}, {'geoClicks': False, 'geoClicksUnique': False, 'geoImpressions': False, 'geoSocialClicks': False, 'geoSocialClicksUnique': False, 'geoSocialImpressions': False}):
            inf = informer_info.get(x['adv'], {})
            domain = inf.get('domain')
            user = inf.get('user')
            key = (user, domain)
            data = domain_data.setdefault(key, {'clicks': 0,
                                                 'imps': 0})
            data['clicks'] += x.get('clicks', 0)
            data['imps'] += x.get('impressions', 0)

        result = {}
        for k, v in domain_data.items():
            user = k[0]
            result.setdefault(user, 0)
            if v['clicks'] > 0 or v['imps'] >= 100:
                result[user] += 1

        return result


    def account_CTR_for_period(self, user_login, start_date, end_date):
        ''' CTR аккаунта ``user_login`` за период от ``start_date`` до ``end_date`` '''

        start_date = h.trim_time(start_date)
        end_date = h.trim_time(end_date)
        ads = [x['guid'] for x in app_globals.db.informer.find({'user': user_login})]
        date_cond = {'$gte': start_date, '$lte': end_date}   
                                           
        clicks_imp = app_globals.db.stats_daily_adv.group([],
                                     {'adv': {'$in': ads},
                                      'date': date_cond},
                                     {'clicksUnique': 0, 'impressions': 0},
                                     'function(o,p) {p.clicksUnique += o.clicksUnique; p.impressions += o.impressions;}')
        try:
            ctr = float(100*clicks_imp[0].get('clicksUnique')) / \
                  float(clicks_imp[0].get('impressions'))
        except:
            ctr = 0
        return ctr

    def account_CTR_block_for_period(self, user_login, start_date, end_date):
        ''' CTR аккаунта ``user_login`` за период от ``start_date`` до ``end_date`` '''

        start_date = h.trim_time(start_date)
        end_date = h.trim_time(end_date)
        ads = [x['guid'] for x in app_globals.db.informer.find({'user': user_login})]
        date_cond = {'$gte': start_date, '$lte': end_date}   
                                           
        clicks_imp = app_globals.db.stats_daily_adv.group([],
                                     {'adv': {'$in': ads},
                                      'date': date_cond},
                                     {'clicksUnique': 0, 'impressions_block': 0},
                                     'function(o,p) {p.clicksUnique += isNaN(o.clicksUnique)? 0 : o.clicksUnique; p.impressions_block += isNaN(o.impressions_block)? 0 : o.impressions_block;}')
        try:
            ctr = float(100*clicks_imp[0].get('clicksUnique')) / \
                  float(clicks_imp[0].get('impressions_block'))
        except:
            ctr = 0
        return ctr
    
    def _usersList(self):
        """ Возвращает список пользователей """
        users_condition = {'manager': {'$ne' : True}}
        users  = [{'login': x['login'], 'registrationDate': x['registrationDate']} for x in app_globals.db.users.find(users_condition).sort('registrationDate')]
        return users
    
    def adsPeriodSummImp(self, ads, dateCond):
        ''' Возвращает сумму и количество показов выгрузки за период ``dateCond``'''
        income = app_globals.db.stats_daily_adv.group([],
                                          {'adv': {'$in': ads}, 'date': dateCond},
                                          {'sum': 0, 'imp': 0, 'imp_block': 0},
                                          'function(o,p) {p.sum += isNaN(o.totalCost)? 0 : o.totalCost; p.imp_block +=isNaN(o.impressions_block)? 0 : o.impressions_block; p.imp +=isNaN(o.impressions)? 0 : o.impressions}')
        try:
            income_summ = float(income[0].get('sum', 0))
            impressions = float(income[0].get('imp', 0))
            impressions_block = float(income[0].get('imp_block', 0))
        except:
            income_summ = 0
            impressions = 0
            impressions_block = 0
        return {'income': income_summ, 'imp': impressions, 'imp_block': impressions_block}
        
    def accountPeriodSummImp(self, user_login):
        ''' Возвращает сумму и количество показов аккаунта за сегодня, 
        вчера, позавчера....'''
        from datetime import date
        ads = [x['guid'] for x in app_globals.db.informer.find({'user': user_login})]
        d = date.today()
        today = datetime(d.year, d.month, d.day)
        one_day = timedelta(days=1)
        two_day = timedelta(days=2)
        one_week = timedelta(weeks=1)
        weekstart = today - one_week
        one_month = timedelta(days=30)
        monthstart = today - one_month
        one_year = timedelta(days=365)
        yearstart = today - one_year
        
        today_cond = datetime(d.year, d.month, d.day)
        yesterday_cond = today - one_day
        before_yesterday_cond = today - two_day
        week_cond = {'$gte': weekstart,'$lte': today} 
        month_cond = {'$gte': monthstart,'$lte': today}
        year_cond = {'$gte': yearstart,'$lte': today}
        
        today = self.adsPeriodSummImp(ads, today_cond)
        yesterday = self.adsPeriodSummImp(ads, yesterday_cond)
        before_yesterday = self.adsPeriodSummImp(ads, before_yesterday_cond)
        week = self.adsPeriodSummImp(ads, week_cond)
        month = self.adsPeriodSummImp(ads, month_cond)
        year = self.adsPeriodSummImp(ads, year_cond)
        
        
        return {'income': {'today': today['income'],
                           'yesterday': yesterday['income'],
                           'before_yesterday': before_yesterday['income'],
                           'week': week['income'],
                           'month': month['income'],
                           'year': year['income']},
                'impressions_block': {'today': today['imp_block'],
                               'yesterday': yesterday['imp_block'],
                               'before_yesterday': before_yesterday['imp_block'],
                               'week': week['imp_block'],
                               'month': month['imp_block'],
                               'year': year['imp_block']},
                'impressions': {'today': today['imp'],
                               'yesterday': yesterday['imp'],
                               'before_yesterday': before_yesterday['imp'],
                               'week': week['imp'],
                               'month': month['imp'],
                               'year': year['imp']}}
        
