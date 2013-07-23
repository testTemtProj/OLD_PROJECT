# -*- coding: utf-8 -*-
import logging

from pylons import request, response, session, tmpl_context as c, url,\
    app_globals
from pylons.controllers.util import abort, redirect

from getmyad.lib.base import BaseController, render
from routes.util import redirect_to
from getmyad.lib import helpers as h
from getmyad import model
from getmyad.model import Account, AccountReports
from datetime import datetime, timedelta
import json
import pymongo.json_util

log = logging.getLogger(__name__)

class ManagerController(BaseController):

    def __before__(self, action, **params):
        user = session.get('user')
        if user and session.get('isManager', False):
            self.user = user
            request.environ['CURRENT_USER'] = user
            request.environ['IS_MANAGER'] = True
        else:
            self.user = ''


    def index(self):
        """Кабинет менеджера"""
        if not self.user: return h.userNotAuthorizedError()
        return render("/manager.mako.html",
                      extra_vars = {'currentClickCost': self.currentClickCost(),
                                    'dataMoneyOutRequests': self.dataMoneyOutRequests(),
                                    'dataUsersSummary': self.dataUsersSummary()})
        
        
    def currentClickCost(self):
        """Возвращает данные для таблицы текущих цен за уникального посетителя"""
        if not self.user: return h.userNotAuthorizedError()
        data =  [{'id': index,
                 'cell': (
                          cost['user_login'],
                          "%.2f" % cost['cost'],
                          cost['date'].strftime("%d.%m.%Y %H:%M") if cost['date'] else ''
                         )
                 }
                for index, cost in enumerate(model.currentClickCost())
                ]
        return json.dumps({'total': 1,
                   'page': 1,
                   'records': len(data),
                   'rows': data
                   },
                   default=pymongo.json_util.default, ensure_ascii=False)


    def setClickCost(self):
        """Устанавливает цену за клик cost для пользователя user начиная со времени date"""
        if not request.environ.get("IS_MANAGER", False): return h.userNotAuthorizedError()
        try:
            cost = float(request.params['cost'])
            user = request.params['user']
            date = h.datetimeFromStr(request.params['date'])
            if cost < 0 or not isinstance(date, datetime):
                raise
        except:
            return h.JSON({'error': 'invalid arguments', 'ok': False})
        
        model.setClickCost(cost, user, '', date)
        return h.JSON({'error': None, 'ok': True})

        
    def dataMoneyOutRequests(self):
        """Возвращает данные для заявок на вывод средств"""
        if not self.user: return h.userNotAuthorizedError()
        data = [(x['user']['login'],
                 x['date'].strftime("%d.%m.%Y %H:%M"),
                 '%.2f $' % x['summ'],
                 u"Да" if x.get('approved', False) else u"Нет",
                 x.get('phone'),
                 x['paymentType'],
                 u'<b>Логин Webmoney:</b> %s<br/><b>Номер счёта Webmoney:</b> %s<br/>' % (x['webmoneyLogin'], x['webmoneyAccount']) +
                    ((u'<b>Примечания:</b>%s'''% (x.get('comment'))) if x.get('comment') else ''))
                for x in app_globals.db.money_out_request.find().sort('date')]
#        return json.dumps(data)
        return h.jgridDataWrapper(data)
    
    
    
    def approveMoneyOut(self):
        """Одобряет заявку пользователя user со временем date (передаются в параметрах)"""
        if not self.user: return h.userNotAuthorizedError()
        user = request.params.get('user')
        date = h.datetimeFromStr(request.params.get('date'))
        t = request.params.get('approved', '').lower()
        if t == 'true':
            approved = True
        elif t == 'false':
            approved = False
        else:
            approved = '' 
        
        if not user or not date or not approved:
            return json.dumps({'error': 'invalid arguments', 'ok': False})

        app_globals.db.money_out_request.update({'user.login': user, 'date': {'$gte': date,
                                                                              '$lte': (date + timedelta(seconds=60))}},
                                                {'$set': {'approved': approved}})

        return json.dumps({'error': None, 'ok': True, 'date': date.strftime("%d.%m.%Y %H:%M"), 'date2': (date + timedelta(seconds=60)).strftime("%d.%m.%Y %H:%M"),})



    def dataUsersSummary(self):
        """Суммарные данные по всем пользователям"""
        if not self.user: return h.userNotAuthorizedError()
        users  = [x['login'] for x in app_globals.db.users.find() if not x.get('manager', False)]
        data = []
        totalSumm = 0
        totalSummMinus = 0
        totalSummToday = 0
        totalSummYesterday = 0
        totalSummWeek = 0
        totalSummMonth = 0
        totalSummYear = 0
        sumDayCTR = 0
        
        for user in users:
            s = AccountReports(Account(user)).balance()
            sYesterday = self.accountYesterdaySumm(user)
            sToday = self.accountTodaySumm(user)
            sWeek = self.accountWeekSumm(user)
            sMonth = self.accountMonthSumm(user)
            sYear = self.accountYearSumm(user)
            dayCTR = self.accountDayCTR(user)
            data.append((user, '%.3f' % dayCTR,
                         h.formatMoney(s),
                         h.formatMoney(sToday),
                         h.formatMoney(sYesterday),
                         h.formatMoney(sWeek),
                         h.formatMoney(sMonth),
                         h.formatMoney(sYear)))
            if s >= 0:
                totalSumm += s
            else: totalSummMinus += s*(-1)    
            totalSummToday += sToday
            totalSummYesterday += sYesterday 
            totalSummWeek += sWeek
            totalSummMonth += sMonth
            totalSummYear += sYear
            sumDayCTR += dayCTR
            
        totalDayCTR = float(sumDayCTR) / float(len(users))  
        totalDayCTR = '%.3f' % totalDayCTR 
            
            
        userdata = {'user': u'ИТОГО:',
                    'summ': h.formatMoney(totalSumm) + ", -" + h.formatMoney(totalSummMinus),
                    'summToday': h.formatMoney(totalSummToday),
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'summWeek': h.formatMoney(totalSummWeek),
                    'summMonth': h.formatMoney(totalSummMonth),
                    'summYear': h.formatMoney(totalSummYear),
                    'dayCTR': totalDayCTR}
        return h.jgridDataWrapper(data, userdata)


    def accountDayCTR(self, user_login):
        ads = [x['guid'] for x in app_globals.db.Advertise.find({'user.login': user_login})]
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)
        monthstart = today - timedelta(days=30) 
        dateCond = {'$gte': monthstart,'$lte': today}   
                                           
        clicks_imp = app_globals.db.stats_daily_adv.group([],
                                     {'adv': {'$in': ads}, 
                                      'date': dateCond},
                                     {'clicksUnique': 0,'impressions':0},
                                     'function(o,p) {p.clicksUnique += o.clicksUnique; p.impressions += o.impressions;}')
        #print clicks_imp.get()
        try:
            ctr = float(100*clicks_imp[0].get('clicksUnique'))/float(clicks_imp[0].get('impressions'))
        except:
            ctr = 0
        return ctr

    def accountTodaySumm(self, user_login):
        """ заработано партнером за сегодня """
        from datetime import date
        d = date.today()
        today = datetime(d.year, d.month, d.day)
        dateCond = today
        return model.accountPeriodSumm(dateCond, user_login)
        
    def accountYesterdaySumm(self, user_login):
        """  заработано партнером за вчера """
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)   
        one_day = timedelta(days=1)
        yesterday = today - one_day
#        print yesterday
        dateCond = yesterday
        return model.accountPeriodSumm(dateCond, user_login)
    
    def accountWeekSumm(self, user_login):
        """ заработано партнером за неделю"""
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)
        one_week = timedelta(weeks=1)
        weekstart = today - one_week
#        print weekstart
        dateCond = {'$gte': weekstart,'$lte': today} 
        return model.accountPeriodSumm(dateCond, user_login)
    
    
    def accountMonthSumm(self, user_login):
        """ заработано партнером за месяц """
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)
        one_month = timedelta(days=30)
        monthstart = today - one_month
#        print monthstart
        dateCond = {'$gte': monthstart,'$lte': today}
        return model.accountPeriodSumm(dateCond, user_login)
        
        
    def accountYearSumm(self, user_login):
        """ заработано партнером за год"""
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)
        one_year = timedelta(days=365)
        yearstart = today - one_year
#        print yearstart
        dateCond = {'$gte': yearstart,'$lte': today}
        return model.accountPeriodSumm(dateCond, user_login)


