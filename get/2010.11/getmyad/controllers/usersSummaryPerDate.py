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
import pymongo.json_util


from getmyad.lib.base import BaseController, render

log = logging.getLogger(__name__)

class UserssummaryperdateController(BaseController):
    
    def dataUsersSummary(self):
        """Суммарные данные по всем пользователям"""

        for user in self._usersList():
            s = AccountReports(Account(user['login'])).balance()
            periodSummImp = self.accountPeriodSummImp(user['login'])
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
            dayCTR = self.account_current_CTR(user['login'])
            activity = self.userActivity(user['login'], date.today())
            activity_yesterday = self.userActivity(user['login'], date.today() - timedelta(days=1))
            activity_before_yesterday = self.userActivity(user['login'], date.today() - timedelta(days=2))
            
            app_globals.db.user.summary_per_date.update({'login': user['login']},
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
                                                 'yesterday': iYesterday,
                                                 'before_yesterday': iBeforeYesterday,
                                                 'week': iWeek,
                                                 'month': iMonth,
                                                 'year': iYear},
                                             'day_CTR': dayCTR,
                                             'summ': s,
                                             'activity': activity,
                                             'activity_yesterday': activity_yesterday,
                                             'activity_before_yesterday': activity_before_yesterday,
                                             'registrationDate': user['registrationDate']
                                            }},
                                            safe=True,
                                            upsert=True)
        current_time = datetime.today()
        app_globals.db.config.update({'key': 'last user.summary_per_date update'}, {'$set': {'value': current_time}}, upsert=True) 
        return


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
        data = model.statGroupedByDate(advertises, dateStart=before_yesterday, dateEnd=today)
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

    def account_current_CTR(self, user_login):
        ''' Текущий CTR аккаунта ``user_login`` '''
        ads = [x['guid'] for x in app_globals.db.informer.find({'user': user_login})]
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)
        start_date = today - timedelta(days=7) 
        date_cond = {'$gte': start_date, '$lte': today}   
                                           
        clicks_imp = app_globals.db.stats_daily_adv.group([],
                                     {'adv': {'$in': ads},
                                      'date': date_cond},
                                     {'clicksUnique': 0, 'impressions': 0},
                                     'function(o,p) {p.clicksUnique += o.clicksUnique; p.impressions += o.impressions;}')
        try:
            ctr = float(100*clicks_imp[0].get('clicksUnique'))/float(clicks_imp[0].get('impressions'))
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
                                          {'sum': 0, 'imp': 0},
                                          'function(o,p) {p.sum += isNaN(o.totalCost)? 0 : o.totalCost; p.imp +=isNaN(o.impressions)? 0 : o.impressions}')
        try:
            income_summ = float(income[0].get('sum', 0))
            impressions = float(income[0].get('imp', 0))
        except:
            income_summ = 0
            impressions = 0
        return {'income': income_summ, 'imp': impressions}
        
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
                'impressions': {'today': today['imp'],
                               'yesterday': yesterday['imp'],
                               'before_yesterday': before_yesterday['imp'],
                               'week': week['imp'],
                               'month': month['imp'],
                               'year': year['imp']}}
        
