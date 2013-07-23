# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from getmyad import model
from getmyad.lib import helpers as h
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
        if not self.user: 
            return redirect('/')
        c.domainsRequests = self.domainsRequests()
        c.dataMoneyOutRequests = self.dataMoneyOutRequests()
        c.managersSummary = self.managersSummary()
        
        c.permission = Permission(Account(self.user))
        if c.permission.has(Permission.REGISTER_USERS_ACCOUNT):
            print '1'
        else: print '2'    
        return render("/manager.mako.html",
                      extra_vars = {'currentClickCost': self.currentClickCost(),
                                    'dataUsersSummary': self.dataUsersSummary()})
        
        
    def managersSummary(self):
        db = app_globals.db
        data = []
        for managerObj in db.users.find({'accountType': 'manager'}):
            manager = managerObj['login']
            totalCost = 0 
            users = [ x['login'] for x in db.users.find({'managerGet': manager} )]
            advs = [x['guid'] for x in db.Advertise.find({'user.login' : {'$in': users}})]
            manager_percent = [(x['date'], x['percent']) for x in db.manager.percent.find({'login': manager})]
#            prev_date = datetime(1900, 1, 1, 0,0,0)
            i = 0
            print sorted(manager_percent, key=lambda row:row[0] )
            now = datetime.today()
            manager_percent.append((datetime(now.year, now.month, now.day, 0,0,0), 0))
            for date_perc in sorted(manager_percent, key=lambda row:row[0] ):
                if (i == 0):
                    prev_date = date_perc[0]
                    percent = date_perc[1]
                    i += 1
                    continue
                costs = db.stats_daily_adv.group([],
                                                {'adv': {'$in': advs},
                                                 'date': 
                                                    {'$gt': prev_date,'$lt': date_perc[0]}},
                                                {'sum': 0, 'i': 0},
                                                'function(o,p) {p.sum += o.totalCost || 0; p.i +=1 }')
                
                for cost in costs:
                        totalCost += cost['sum']*percent
                prev_date =  date_perc[0]
                percent = date_perc[1]
            
             
            
                 
                      
                        
            totalCost = float(totalCost)/float(100)
                  
            data.append((manager, managerObj.get('percent',0), "%.2f" % totalCost))       
        return h.jgridDataWrapper(data)
    
    def setManagerPercent(self):
        """Устанавливает процент менеджера от дохода"""
        if not Permission(Account(self.user)).has(Permission.SET_MANAGER_PERCENT):
            return h.insufficientRightsError()
        try:
            percent = float(request.params['percent'])
            manager_login = request.params['manager']
            if percent < 0 : raise
        except:
            return h.JSON({'error': 'invalid arguments', 'ok': False})
        model.setManagerPercent(manager_login, percent)
        return h.JSON({'error': None, 'ok': True})

    
    
    def setClickCost(self):
        """Устанавливает цену за клик cost для пользователя user начиная со времени date"""
        if not self.user: return h.userNotAuthorizedError()
        if not Permission(Account(self.user)).has(Permission.SET_CLICK_COST): return h.insufficientRightsError()
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

    
    def currentClickCost(self):
        """Возвращает данные для таблицы текущих цен за уникального посетителя"""
        if not self.user: return h.userNotAuthorizedError()
        costs = list(model.currentClickCost())
        
        users = self._usersList()
        data =  [(cost['user_login'],
                  "%.2f" % cost['cost'],
                  cost['date'].strftime("%d.%m.%Y %H:%M") if cost['date'] else '' )
                for cost in costs if cost['user_login'] in users]
        sum_cost = 0
        avg_cost = 0
        for cost in costs:
            if cost['user_login'] in users:
                sum_cost += cost.get('cost', 0);
        try:    
            avg_cost = float(sum_cost) / len(data) 
        except ZeroDivisionError:
            avg_cost = 0
        finally:    
            userdata = {'user': u'Средняя цена за клик',
                        'cost': "%.2f" % avg_cost,
                        'day' : ''
                         }
        return h.jgridDataWrapper(data, userdata)


        
    def dataMoneyOutRequests(self):
        """Возвращает данные для заявок на вывод средств"""
        if not self.user: return h.userNotAuthorizedError()
        if not Permission(Account(login=self.user)).has(Permission.VIEW_MONEY_OUT):
            return h.JSON(None)
        data = [(x['user']['login'],
                 x['date'].strftime("%d.%m.%Y %H:%M"),
                 '%.2f $' % x['summ'],
                 u"Да" if x.get('approved', False) else u"Нет",
                 x.get('phone'),
                 x['paymentType'],
                 u'<b>Логин Webmoney:</b> %s<br/><b>Номер счёта Webmoney:</b> %s<br/>' % (x['webmoneyLogin'], x['webmoneyAccount']) +
                    ((u'<b>Примечания:</b>%s'''% (x.get('comment'))) if x.get('comment') else ''))
                for x in app_globals.db.money_out_request.find().sort('date')]
        return h.jgridDataWrapper(data)
    
    
    
    def approveMoneyOut(self):
        """Одобряет заявку пользователя user со временем date (передаются в параметрах)"""
        if not self.user: return h.userNotAuthorizedError()
        if not Permission(Account(login=self.user)).has(Permission.VIEW_MONEY_OUT):
            return h.insufficientRightsError()
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
        if not self.user:
            return redirect(url_for(action="main", controller="index")) 


        users = self._usersList()
#        print users
        data = []
        totalSumm = 0
        totalSummMinus = 0
        totalSummToday = 0
        totalSummYesterday = 0
        totalSummBeforeYesterday = 0
        totalSummWeek = 0
        totalSummMonth = 0
        totalSummYear = 0
        sumDayCTR = 0
        
        for user in users:
            s = AccountReports(Account(user)).balance()
            sYesterday = self.accountYesterdaySumm(user)
            sBeforeYesterday = self.accountBeforeYesterdaySumm(user)
            sToday = self.accountTodaySumm(user)
            sWeek = self.accountWeekSumm(user)
            sMonth = self.accountMonthSumm(user)
            sYear = self.accountYearSumm(user)
            dayCTR = self.accountDayCTR(user)
            data.append((user, '%.3f' % dayCTR,
                         h.formatMoney(s),
                         h.formatMoney(sToday),
                         h.formatMoney(sYesterday),
                         h.formatMoney(sBeforeYesterday),
                         h.formatMoney(sWeek),
                         h.formatMoney(sMonth),
                         h.formatMoney(sYear)))
            if s >= 0:
                totalSumm += s
            else: totalSummMinus += s*(-1)    
            totalSummToday += sToday
            totalSummYesterday += sYesterday
            totalSummBeforeYesterday += sBeforeYesterday 
            totalSummWeek += sWeek
            totalSummMonth += sMonth
            totalSummYear += sYear
            sumDayCTR += dayCTR

        try:            
            totalDayCTR = float(sumDayCTR) / float(len(users))
        except ZeroDivisionError:
            totalDayCTR = 0  
        totalDayCTR = '%.3f' % totalDayCTR 
            
            
        userdata = {'user': u'ИТОГО:',
                    'summ': h.formatMoney(totalSumm) + ", -" + h.formatMoney(totalSummMinus),
                    'summToday': h.formatMoney(totalSummToday),
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'summBeforeYesterday': h.formatMoney(totalSummBeforeYesterday),
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
    
    def accountBeforeYesterdaySumm(self, user_login):
        """  заработано партнером за позавчера """
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)   
        two_day = timedelta(days=2)
        yesterday = today - two_day
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


    def domainsRequests(self):
        ''' Возвращает список заявок на регистрацию домена '''
        if not self.user: return h.userNotAuthorizedError()
        if not Permission(Account(self.user)).has(Permission.USER_DOMAINS_MODERATION): return h.jgridDataWrapper([])
        result = []
        for user_item in app_globals.db['user.domains'].find({'requests': {'$exists': True}}):
            for request in user_item['requests']:
                row = (user_item['login'], '', request, '')
                result.append(row)
        return h.jgridDataWrapper(result)
        
        
    def approveDomain(self):
        ''' Одобряет заявку на регистрацию домена '''
        if not self.user: return h.userNotAuthorizedError()
        if not Permission(Account(self.user)).has(Permission.VIEW_MONEY_OUT): return h.insufficientRightsError() 
        try:
            user = request.params['user'] 
            domain = request.params['domain']
            account = Account(login=user)
            account.domains.approve_request(domain)
            return h.JSON({'error': False})
        except KeyError:
            return h.JSON({'error': True, 'message': 'params error'})
        except:
            return h.JSON({'error': True})
        
        
        
    def _usersList(self):
        """ Возвращает список пользователей """
        if not self.user: return []
        users_condition = {'manager': {'$ne' : True}}
        if not Permission(Account(login=self.user)).has(Permission.VIEW_ALL_USERS_STATS):
            users_condition.update({'managerGet': self.user})
#        print users_condition    
        users  = [x['login'] for x in app_globals.db.users.find(users_condition)]
        
        return users
    
    
    
    def userDetails(self):
        """ Вкладка детальной информации о пользователе """
        c.login = request.params.get('login')
        if not c.login:
            return "Неверно указаны параметры"
        return render("administrator/user-details.mako.html")
    
    
    
    
    