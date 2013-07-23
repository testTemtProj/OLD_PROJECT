# -*- coding: utf-8 -*-
from datetime import datetime, date, time, timedelta
from formencode import Schema, validators as v
from getmyad import model
from getmyad.lib import helpers as h
from getmyad.lib.base import BaseController, render
from getmyad.model import Account, AccountReports, Permission, mq
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals, config
from pylons.controllers.util import abort, redirect
from routes.util import url_for
from uuid import uuid1
import formencode
import json
import logging
import os
import pymongo
import re
import base64


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
            return h.userNotAuthorizedError()                    # TODO: Ошибку на нормальной странице     
        return f(*args)
    return wrapper

def authcheck(f):
    ''' Декоратор сравнивает текущего пользователя и пользователя, от которого пришёл запрос. ''' 
    def wrapper(*args):
        try:
            if c.info['user'] != session.get('user'): raise
        except NameError:
            raise TypeError("Не задана переменная info во время вызова authcheck")
        except:
            return h.userNotAuthorizedError()                    # TODO: Ошибку на нормальной странице
        return f(*args)
    return wrapper 


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
        
        token = str(uuid1()).upper()
        session[token] = {'user': session.get('user')}
        session.save()
        c.token = token      
        
        c.domainsRequests = self.domainsRequests()
        c.dataMoneyOutRequests = self.dataMoneyOutRequests()
        c.managersSummary = self.managersSummary()
        c.dataOverallSummary = self.overallSummaryByDays()
        c.account = model.Account(login=self.user)
        c.account.load()
        c.permission = Permission(c.account)
        c.date = self.todayDateString()
        c.acc_count = len(self._usersList())
        c.sum_out = self.sumOut() 
        c.prognoz_sum_out = '%.2f $' % self.prognozSumOut()
        
        act_acc_count = self.activeAccountCount()
        c.act_acc_count = act_acc_count.get('today')
        c.act_acc_count_yesterday = act_acc_count.get('yesterday')
        c.act_acc_count_b_yesterday = act_acc_count.get('before_yesterday')                
        c.notApprovedRequests = self.notApprovedActiveMoneyOutRequests()
        c.moneyOutHistory = self.moneyOutHistory()
        c.dataUsersImpressions = self.dataUsersImpressions()
        c.usersSummaryActualTime = self.usersSummaryActualTime() 
        
        return render("/manager.mako.html",
                      extra_vars={'currentClickCost': self.currentClickCost(),
                                    'dataUsersSummary': self.dataUsersSummary()})
        
        
    def usersSummaryActualTime(self):
        ''' Время на которое актуальны данные статистики'''
        try:
            x = app_globals.db.config.find_one({'key': 'last user.summary_per_date update'})
            actualTime = x.get('value')
            actualTime = actualTime.strftime('%H:%M %d.%m.%Y')
        except:
            actualTime = ''
        return actualTime
      
    def todayDateString(self): 
        monthNames = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
        now = datetime.today()
        return str(now.day) + ' ' + monthNames[now.month - 1] + ' ' + str(now.year) + ',  ' + str(now.time())[:8]
           
    def activeAccountCount(self):
        '''Кол-во аккаунтов сегодня и в предыдущие дни'''
        act_acc_count = 0
        yest_act_acc_count = 0
        b_yest_act_acc_count = 0
        users = self._usersList()
        for x in app_globals.db.user.summary_per_date.find():
            try:
                if x['login'] not in users: continue
                if x['activity'] == 'greenflag':
                    act_acc_count += 1 
                if x['activity_yesterday'] == 'greenflag':
                    yest_act_acc_count += 1
                if x['activity_before_yesterday'] == 'greenflag':
                    b_yest_act_acc_count += 1
            except KeyError:
                pass
        return {'today': act_acc_count,
                'yesterday': yest_act_acc_count,
                'before_yesterday': b_yest_act_acc_count}
        
    def managersSummary(self):
        ''' Данные для таблицы данных о менеджерах''' 
        db = app_globals.db
        data = []
        for manager in db.users.find({'accountType': 'manager', 'hidden': {'$ne': True}}):
            balance = model.ManagerReports(Account(manager['login'])).balance()
            data.append((manager['login'], manager.get('percent', 0), "%.2f" % balance))       
        return h.jgridDataWrapper(data)
    
    @current_user_check 
#    @expandtoken    
#    @authcheck    
    def overallSummaryByDays(self):
        ''' Данные для таблицы суммарных данных по дням '''
        data = []
        for x in app_globals.db.stats_overall_by_date.find().sort('date', pymongo.DESCENDING):
            ctr = 100.0 * x['clicksUnique'] / x['impressions'] if x['impressions'] else 0
            click_cost_avg = x['totalCost'] / x['clicksUnique'] if x['clicksUnique'] else 0
            row = (x['date'].strftime("%d.%m.%Y"),
                   int(x['impressions']),
                   int(x['clicksUnique']),
                   h.formatMoney(x['totalCost']),
                   '%.3f' % ctr,
                   '%.2f ¢' % (click_cost_avg * 100)
                   )
            data.append(row)
        return h.jgridDataWrapper(data)
    
    @current_user_check 
    @expandtoken    
    @authcheck    
    def setManagerPercent(self):
        """Устанавливает процент менеджера от дохода"""
        try:
            percent = float(request.params['percent'])
            manager_login = request.params['manager']
            if percent < 0 : raise
        except:
            return h.JSON({'error': True, 'msg': 'invalid arguments', 'ok': False})
        model.setManagerPercent(manager_login, percent)
        return h.JSON({'error': False, 'ok': True})

    
    @current_user_check 
    @expandtoken    
    @authcheck    
    def setClickCost(self):
        """Устанавливает цену за клик cost для пользователя user начиная со времени date"""
        if not Permission(Account(self.user)).has(Permission.SET_CLICK_COST): return h.insufficientRightsError()
        try:
            cost = float(request.params['cost'])
            user = request.params['user']
            date = h.datetimeFromStr(request.params['date'])
            if cost < 0 or not isinstance(date, datetime):
                raise
        except:
            return h.JSON({'error': True, 'msg': 'invalid arguments', 'ok': False})
        model.setClickCost(cost, user, '', date)
        return h.JSON({'error': False, 'ok': True})

    
    def currentClickCost(self):
        """ Возвращает данные для таблицы текущих цен за уникального посетителя.
            
            Принимает get-параметр onlyActive. Если он равен true, то возвращает
            цены только для активных аккаунтов. По умолчанию равен false. 
            TODO: Параметр указывающий, порядок ответа(обратная сортировка, и по какому столбцу)        """
        if not self.user: return h.userNotAuthorizedError()
        costs = list(model.currentClickCost())
        users = self._usersList()
        filter_inactive = request.params.get('onlyActive', 'false') == 'true'
        if filter_inactive:
            active_users = [x.get('login') for x in
                                app_globals.db.user.summary_per_date.find({'activity': 'greenflag'})]
            users = set(users).intersection(set(active_users))
        
        data = [(cost['user_login'],
                  "%.2f" % cost['cost'],
                  cost['date'].strftime("%d.%m.%Y %H:%M") if cost['date'] else '')
                for cost in costs if cost['user_login'] in users]
        sum_cost = 0
        avg_cost = 0
        for cost in costs:
            if cost['user_login'] in users:
                sum_cost += cost.get('cost', 0)
        try:    
            avg_cost = float(sum_cost) / len(data) 
        except ZeroDivisionError:
            avg_cost = 0
        finally:    
            userdata = {'user': u'Средняя цена за клик',
                        'cost': "%.3f" % avg_cost,
                        'day' : ''}
        #Типа сортировка, нужно облагородить            
        iCol = int(request.params.get('sortCol', 0))
        if request.params.get('sortRevers')=="True":
            r=True
        else:            
            r=False        
        data.sort(key=lambda x: x[iCol-1], reverse = r)        
        return h.jgridDataWrapper(data, userdata)


    def prognozSumOut(self):
        'Возвращает прогнозируемую сумму к выводу на ближайшее 10-е число'
        today = datetime.today()
        one_month = timedelta(days=30)
        if today.day > 10:
            month_day_10 = today + one_month
            month_day_10 = datetime(today.year, month_day_10.month, 10)
        else:
            month_day_10 = datetime(today.year, today.month, 10)
        daysdelta = month_day_10 - today

#        users = self._usersList()
        calc_sum_out = 0
        for x in app_globals.db.user.summary_per_date.find():
            try:
                month_sum = x['income']['month']
            except KeyError:
                month_sum = 0
            avg_day_sum = float(month_sum) / 30
            sum = avg_day_sum * daysdelta.days
            try:
                data = app_globals.db.users.find_one({'login': x['login']})
                min_out_sum = float(data['min_out_sum'])
            except:
                min_out_sum = 100
            if sum >= min_out_sum:
                calc_sum_out += sum
            
        return calc_sum_out + self.sumOut()['total']


    def sumOut(self):
        """ Возвращает сумму доступную к выводу на сегодня с разбиением по 
            предполагаемым способам вывода.
        
            Способ вывода пытается определить на основании последнего
            использованного метода (хранится с поле lastPaymentType коллекции
            users). Если выводов ещё не было, то смотрит на доступные методы.
            Если доступен только один какой-либо, то приписывает сумму к нему.
            Если доступно более одного способа, относит сумму к неопределённым 
            методам ('unknown').            
            
            Возвращает структуру вида::
            
                { 'total': 100.0,        # Общая сумма к выводу
                  'webmoney_z': 50.0,    # \
                  'card': 10.0,          #  > Сумма вывода каждым методом
                  'factura': 15.0,       # /
                  'unknown': 25.0        # Не удалось определить метод
                }
                
        """
        
        result = {'total': 0.0,
                  'webmoney_z': 0.0,
                  'card': 0.0,
                  'factura': 0.0,
                  'unknown': 0.0}
        
        for x in app_globals.db.user.summary_per_date.find():
            try:
                user_data = app_globals.db.users.find_one({'login': x['login']})
                min_out_sum = float(user_data['min_out_sum'])
            except (KeyError, ValueError, TypeError):
                min_out_sum = 100

            if user_data:
                if user_data.get('lastPaymentType'):
                    payment_type = user_data.get('lastPaymentType')
                elif len(user_data.get('moneyOutPaymentType', [])) == 1:
                    payment_type = user_data.get('moneyOutPaymentType')[0]
                elif not user_data.get('moneyOutPaymentType'):
                    payment_type = 'webmoney_z'
                else:
                    payment_type = 'unknown'
            else:
                payment_type = 'unknown'

            accountSumm = x.get('summ', 0)
            if accountSumm >= min_out_sum:
                result[payment_type] += accountSumm
                result['total'] += accountSumm
                
        return result
    
    
    def tableForDataMoneyOutRequest(self, data_from_db):
        '''Возвращает форматированные данные для jgrid.
           На входе принимает результат запроса к 
           db.money_out_request'''
        
        def commentFormat(str):
            ''' Форматирует строку вывода'''
            if not str: return ''
            str = str.replace('\n', ' ')
            res = ['']
            j = 0
            for sub in str.split(' '):
                if len(res[j] + sub + ' ') > 40:
                    res[j] += '\n'
                    j += 1
                    res.append('')
                res[j] += sub + ' '
            import string     
            return string.join(res)
        
        if not self.user: return h.userNotAuthorizedError()
        if not Permission(Account(login=self.user)).has(Permission.VIEW_MONEY_OUT):
            return h.JSON(None)
        data = []
        for x in data_from_db:
            login = x['user']['login']
            date = x.get('date').strftime("%d.%m.%Y %H:%M")
            summ = '%.2f $' % x['summ']
            if x.get('user_confirmed'):
                user_confirmed = u"Да"
            else:
                user_confirmed = u"Нет"    
            if x.get('approved', False):
                approved = u"Да"
            else:
                approved = u"<b style='color: red;'>Нет</b>"    
            phone = x.get('phone')   
            paymentType = u'счёт-фактура' if x.get('paymentType') == 'factura' else x.get('paymentType') 
             
            if x.get('paymentType') == 'webmoney_z': 
                comment = (u'<b>Логин Webmoney:</b> %s<br/>' + 
                           u'<b>Номер счёта Webmoney:</b> %s<br/>')% (x['webmoneyLogin'], x['webmoneyAccount'])
            elif x.get('paymentType') == 'card':
                comment = (u'<b>Банк:</b> %s <br/>' \
                           u'<b>Номер пластиковой карты:</b> %s<br/>' \
                           u'<b>Имя владельца карты:</b> %s <br/>' \
                           u'<b>Срок действия карты:</b> %s/%s <br/>' \
                           u'<b>Валюта и тип карты:</b> %s %s<br/>' \
                           u'<b>МФО банка:</b> %s <br/>' \
                           u'<b>ОКПО банка:</b> %s <br/>' \
                           u'<b>Транзитный счёт:</b> %s <br/>' \
                           ) \
                            % (x.get('bank'),
                               x.get('cardNumber'), 
                               x.get('cardName'), 
                               x.get('expire_month'),
                               x.get('expire_year'),
                               x.get('cardCurrency', ''),
                               x.get('cardType', ''),
                               x.get('bank_MFO', ''),
                               x.get('bank_OKPO', ''),
                               x.get('bank_TransitAccount', ''))
            elif x.get('paymentType') == 'factura':
                comment = (u'<b>Контакты:</b> %s<br/>' +
                           u'<a href="/manager/openSchetFacturaFile?filename=%s" class="facturaLink" target="_blank">' + 
                           u'Счёт-фактура</a><br/>') \
                           %(x.get('contact'),
                             x.get('schet_factura_file_name'))

            else:
                comment = u''                         
            
            if x.get('comment'):
                comment += u'<b>Примечания:</b> %s ' % commentFormat(x.get('comment'))               
            
            
            data.append((login, date, summ, user_confirmed, approved, phone, paymentType, comment ))                
        return h.jgridDataWrapper(data)   
    
        

    def dataMoneyOutRequests(self):
        """Возвращает данные для таблицы со списком заявок на вывод средств"""
        data_from_db = app_globals.db.money_out_request.find().\
                                    sort('date', pymongo.DESCENDING)
        return self.tableForDataMoneyOutRequest(data_from_db)                            
        
    
    def notApprovedActiveMoneyOutRequests(self):
        ''' Количество неодобреных заявок на вывод средств'''
        count = 0
        today = datetime.today()
        three_days_ago = today - timedelta(days=3)
        for x in app_globals.db.money_out_request.group([],
                                    {'approved': {'$ne': True},
                                     'date': {'$gt': three_days_ago}},
                                    {'count': 0},
                                    'function(o,p) {p.count += 1};'):
            count = x['count']
        return str(int(count))
#        return h.JSON({'count': count})
    
    @current_user_check 
    @expandtoken    
    @authcheck 
    def approveMoneyOut(self):
        """Одобряет заявку пользователя user со временем date (передаются в параметрах)"""
        if not Permission(Account(login=self.user)).has(Permission.VIEW_MONEY_OUT):
            return h.insufficientRightsError()
        
        user = request.params.get('user')
        user = re.findall("<.*>(.*)</.*>", user)[0]
        date = h.datetimeFromStr(request.params.get('date'))
        t = request.params.get('approved', '').lower()
        if t == 'true':
            approved = True
        elif t == 'false':
            approved = False
        else:
            approved = '' 
        
        if not user or not date or not approved:
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        # Обновляем заявку
        db = app_globals.db
        money_out_request = \
            db.money_out_request.find_one({'user.login': user,
                                           'date': {'$gte': date,
                                                    '$lte': (date + timedelta(seconds=60))}})
        money_out_request['approved'] = approved
        db.money_out_request.save(money_out_request, safe=True)
        
        # Обновляем последний метод вывода средств для пользователя 
        db.users.update({'login': user},
                        {'$set': {'lastPaymentType': money_out_request.get('paymentType', '')}},
                        safe=True)

        return json.dumps({'error': False, 'ok': True, 'date': date.strftime("%d.%m.%Y %H:%M"), 'date2': (date + timedelta(seconds=60)).strftime("%d.%m.%Y %H:%M")})


    def dataUsersImpressions(self):
        """Суммарные данные по всем пользователям по количеству показов"""
        users = self._usersList()
        data = []
        totalImpToday = 0
        totalImpYesterday = 0
        totalImpBeforeYesterday = 0
        totalImpWeek = 0
        totalImpMonth = 0
        totalImpYear = 0
        if int(request.params.get('sortCol', -1)) >= 0:  
            for x in app_globals.db.user.summary_per_date.find().sort('registrationDate'):
                if x['login'] not in users: continue
                data.append(('<a href="javascript:;" class="actionLink %s" >%s</a>'%(x['activity'],x['login']),
                            x['impressions']['today'],
                            x['impressions']['yesterday'],
                            x['impressions']['before_yesterday'],
                            x['impressions']['week'],
                            x['impressions']['month'],
                            x['impressions']['year'],
                            2 if x['activity'] == "greenflag" else 1))
                totalImpToday += x['impressions']['today']
                totalImpYesterday += x['impressions']['yesterday']
                totalImpBeforeYesterday += x['impressions']['before_yesterday'] 
                totalImpWeek += x['impressions']['week']
                totalImpMonth += x['impressions']['month']
                totalImpYear += x['impressions']['year']
            userdata = {'user': u'ИТОГО:',
                        'impToday': totalImpToday,
                        'impYesterday': totalImpYesterday,
                        'impBeforeYesterday': totalImpBeforeYesterday,
                        'impWeek': totalImpWeek,
                        'impMonth': totalImpMonth,
                        'impYear': totalImpYear
                        }
        else:
            for x in app_globals.db.user.summary_per_date.find().sort('registrationDate'):
                if x['login'] not in users: continue
                data.append((x['login'],
                            x['impressions']['today'],
                            x['impressions']['yesterday'],
                            x['impressions']['before_yesterday'],
                            x['impressions']['week'],
                            x['impressions']['month'],
                            x['impressions']['year'],
                            x['activity']))
                totalImpToday += x['impressions']['today']
                totalImpYesterday += x['impressions']['yesterday']
                totalImpBeforeYesterday += x['impressions']['before_yesterday'] 
                totalImpWeek += x['impressions']['week']
                totalImpMonth += x['impressions']['month']
                totalImpYear += x['impressions']['year']
            userdata = {'user': u'ИТОГО:',
                        'impToday': totalImpToday,
                        'impYesterday': totalImpYesterday,
                        'impBeforeYesterday': totalImpBeforeYesterday,
                        'impWeek': totalImpWeek,
                        'impMonth': totalImpMonth,
                        'impYear': totalImpYear
                        }
            return h.jgridDataWrapper(data, userdata)
        iCol = int(request.params.get('sortCol', 0))                        
        if request.params.get('sortRevers')=="True":
            r=True
        else:
            r=False
#        if iCol == 1:
#            data.sort(key=lambda x: x[7], reverse = r)
#        else:                
        data.sort(key=lambda x: x[iCol-1], reverse = r)        
        return h.jgridDataWrapper(data, userdata)


    def dataUsersSummary(self):
        """Суммарные данные по всем пользователям"""
        users = self._usersList()
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
        if int(request.params.get('sortCol', -1)) < 0:   
            for x in app_globals.db.user.summary_per_date.find().sort('registrationDate'):
                if x['login'] not in users: continue
                data.append((x['login'],
                            h.formatMoney(x['income']['today']),
                            h.formatMoney(x['income']['yesterday']),
                            h.formatMoney(x['income']['before_yesterday']),
                            h.formatMoney(x['income']['week']),
                            h.formatMoney(x['income']['month']),
                            h.formatMoney(x['income']['year']),
                            '%.3f' % x['day_CTR'],
                            h.formatMoney(x['summ']),
                            x['activity']))
                if x['summ'] >= 0:
                    totalSumm += x['summ']
                else: totalSummMinus += x['summ'] * (-1)    
                totalSummToday += x['income']['today']
                totalSummYesterday += x['income']['yesterday']
                totalSummBeforeYesterday += x['income']['before_yesterday'] 
                totalSummWeek += x['income']['week']
                totalSummMonth += x['income']['month']
                totalSummYear += x['income']['year']
                sumDayCTR += x['day_CTR']
    
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
        else:
            for x in app_globals.db.user.summary_per_date.find().sort('registrationDate'):
                if x['login'] not in users: continue
                data.append(('<a href="javascript:;" class="actionLink %s" >%s</a>'%(x['activity'],x['login']),
                            h.formatMoney(x['income']['today']),
                            h.formatMoney(x['income']['yesterday']),
                            h.formatMoney(x['income']['before_yesterday']),
                            h.formatMoney(x['income']['week']),
                            h.formatMoney(x['income']['month']),
                            h.formatMoney(x['income']['year']),
                            '%.3f' % x['day_CTR'],
                            h.formatMoney(x['summ']),
                            2 if x['activity'] == "greenflag" else 1))
                if x['summ'] >= 0:
                    totalSumm += x['summ']
                else: totalSummMinus += x['summ'] * (-1)    
                totalSummToday += x['income']['today']
                totalSummYesterday += x['income']['yesterday']
                totalSummBeforeYesterday += x['income']['before_yesterday'] 
                totalSummWeek += x['income']['week']
                totalSummMonth += x['income']['month']
                totalSummYear += x['income']['year']
                sumDayCTR += x['day_CTR']
    
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
        iCol = int(request.params.get('sortCol', 0)) 
        r = (request.params.get('sortRevers') == "desc")
        if iCol >= 2:
            data.sort(key=lambda x: float(str(x[iCol-1].partition(' ')[0])), reverse = r)
        else:
            data.sort(key=lambda x: x[iCol-1], reverse = r)         
        return h.jgridDataWrapper(data, userdata)


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
            ctr = float(100 * clicks_imp[0].get('clicksUnique')) / float(clicks_imp[0].get('impressions'))
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
        dateCond = {'$gte': weekstart, '$lte': today} 
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
        
    
    @current_user_check 
    @expandtoken    
    @authcheck     
    def approveDomain(self):
        ''' Одобряет заявку на регистрацию домена '''
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
        
    @current_user_check 
    @expandtoken    
    @authcheck     
    def rejectDomain(self):
        ''' Отклоняет заявку на регистрацию домена '''
        if not Permission(Account(self.user)).has(Permission.VIEW_MONEY_OUT): return h.insufficientRightsError() 
        try:
            user = request.params['user'] 
            domain = request.params['domain']
            account = Account(login=user)
            account.domains.reject_request(domain)
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
        users = [x['login'] for x in app_globals.db.users.find(users_condition).sort('registrationDate')]
        return users
    
    
    @current_user_check
    def userDetails(self):
        """ Вкладка детальной информации о пользователе """
        c.permission = Permission(Account(login=self.user))
        c.login = request.params.get('login')
        c.token = request.params.get('token')
        c.div_to_open = h.JSON(request.params.get('div'))
        if not c.login:
            return h.JSON({"error": True, 'msg': u'Неверно указаны параметры', 'ok': False})
        edit_account = model.Account(c.login)
        edit_account.load()
        c.edit_min_out_sum = edit_account.min_out_sum
        c.edit_manager_get = edit_account.manager_get
        c.list_manager = [x['login'] for x in app_globals.db.users.find({'manager': True})]
        c.edit_name = edit_account.owner_name
        c.edit_phone = edit_account.phone
        c.edit_email = edit_account.email
        c.edit_money_web_z = 'webmoney_z' in edit_account.money_out_paymentType
        c.edit_money_card = 'card' in edit_account.money_out_paymentType
        c.edit_money_factura = 'factura' in edit_account.money_out_paymentType
        c.edit_account_error_messages = ''
        c.edit_prepayment = edit_account.prepayment
        c.edit_account_blocked = edit_account.blocked or ''
        c.account_domains = edit_account.domains.list()
        c.domains_categories = {}
        for x in c.account_domains:
            categories = [y['categories'] for y in app_globals.db.domain.categories.find({'domain': x}) or []]
            if len(categories) > 0:
                c.domains_categories[x] = categories[0]
            else:
                c.domains_categories[x] = []
        c.categories = [{'title': x['title'], 'guid': x['guid']} for x in app_globals.db.advertise.category.find()]
        c.accountMoneyOutHistory = self.accountMoneyOutHistory(c.login)
        c.accountSumm = edit_account.report.balance()
        c.prepayment = edit_account.prepayment
        #return render("administrator/user-details.mako.html#edit-domain-categories")
        return render("administrator/user-details.mako.html")
    
    @current_user_check
    @expandtoken    
    @authcheck 
    def setNewPassword(self):
        ''' Устанавливает новый пароль для пользователя''' 
        try:
            password = request.params['psw']
            login = request.params['login']
            app_globals.db.users.update({'login': login}, {'$set': {'password': password}})
            return h.JSON({'error': False})
        except:    
            return h.JSON({'error': True})
        
    def generateNewPassword(self):
        ''' Генерирует пароль'''
        try:
            new_password = model.makePassword()
            return h.JSON({'error': False, 'new_password': new_password})
        except:
            return h.JSON({'error': True})
    
    class PaymentTypeNotDefined(Exception):
        ''' Не выбран ни один способ вывода средств '''
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return 'PaymentTypeNotDefined'
        
        
        
    @current_user_check 
    @expandtoken    
    @authcheck
    def checkCurrentUser(self):
        ''' Функция для проверки аутентичности пользователя и токена, 
        возвращает только статус проверки и ничего не делает'''
        return h.JSON({"error": False})        
        

    @current_user_check 
    @expandtoken    
    @authcheck     
    def saveUserDetails(self):
        """ Сохранение информации о пользователе """
        c.login = request.params.get('login')
        edit_account = model.Account(c.login)
        edit_account.load()
        schema = updateUserForm()
        try: 
            form_result = schema.to_python(dict(request.params))
            c.edit_money_card = False if not request.params.get('edit_money_card') else True
            c.edit_money_web_z = False if not request.params.get('edit_money_web_z') else True
            c.edit_money_factura = False if not request.params.get('edit_money_factura') else True
            if (not c.edit_money_card and not c.edit_money_web_z and not c.edit_money_factura):
                    raise ManagerController.PaymentTypeNotDefined('Payment_type_not_defined')
        except formencode.Invalid, error:
            return h.JSON({'error': True, 'msg': '\n'.join([x.msg for x in error.error_dict.values()])})
        except self.PaymentTypeNotDefined:
            return h.JSON({'error': True, 'msg': u'Укажите хотя бы один способ вывода средств!'})
                      
        edit_account.min_out_sum = request.params.get('edit_minsum')
        edit_account.owner_name = request.params.get('edit_name')
        edit_account.manager_get = request.params.get('edit_manager_get')
        edit_account.phone = request.params.get('edit_phone')
        edit_account.email = request.params.get('edit_email')
        edit_account.money_card = False if not request.params.get('edit_money_card') else True
        edit_account.money_web_z = False if not request.params.get('edit_money_web_z') else True
        edit_account.money_factura = False if not request.params.get('edit_money_factura') else True
        edit_account.prepayment = False if not request.params.get('edit_prepayment') else True
        edit_account.blocked = request.params.get('edit_account_blocked', False)
        edit_account.update()
        return h.JSON({'error': False})
    
    @current_user_check
    @expandtoken    
    @authcheck 
    def saveDomainCategories(self):
        '''Сохранение настроек категорий для домена аккаунта'''
        try:
            categories = request.params.getall('categories')
            domain = request.params.get('account_domains')
            if len(domain) == 0:
                return h.JSON({'error': True, 'msg': u'Ошибка! Не указан домен!'})
            app_globals.db.domain.categories.update({'domain': domain},
                                                    {'$set':
                                                           {'categories': categories} 
                                                     },
                                                     upsert=True)
            login = request.params.get('login')
            edit_account = model.Account(login)
            edit_account.load()
            account_domains = edit_account.domains.list()
            domains_categories = {}
            for x in account_domains:
                categories = [y['categories'] for y in app_globals.db.domain.categories.find({'domain': x})]
                if len(categories) > 0:
                    domains_categories[x] = categories[0]
                else:     
                    domains_categories[x] = []
            try:
                mq.MQ().account_update(login)
            except:
                return h.JSON({'error': True,
                               'msg': u'Сохранения изменены, но из-за ошибки AMQP временно не будут применяться. Свяжитесь с администратором. '})
        except:
            return h.JSON({'error': True})
            
        return h.JSON({'error': False, 'domains_categories': domains_categories})

    @current_user_check 
    @expandtoken    
    @authcheck 
    def moneyOutSubmit(self):
        ''' Заявка от менеджера на вывод его средств'''
        schema = MoneyOutForm()
        try:
            form = schema.to_python(dict(request.params))
        except formencode.Invalid, error:
            errorMessage = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
            return json.dumps({'error': True, 'msg': errorMessage, 'ok': False}, ensure_ascii=False)
        
        app_globals.db.money_out_request.insert(
                        {
                             'date': datetime.now(),
                             'user': {'guid': '',
                                      'login': c.manager_login},
                             'summ': form.get('moneyOut_summ'),
                             'comment': form.get('moneyOut_comment')
                        })
        return json.dumps({'error': False, 'ok': True, 'msg': 'Заявка успешно принята'})
    
    def moneyOutHistory(self):
        """История вывода денег"""
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()

        data = AccountReports(Account(user)).money_out_requests()
        data.sort(key=lambda x:x['date'])
        
        table = [(x['date'].strftime("%d.%m.%Y"),
                  '%.2f $' % x['summ'],
                  x.get('comment') if x.get('approved') else u'заявка обрабатывается...')
                 for x in data]
        return h.jgridDataWrapper(table)
    
    def accountMoneyOutHistory(self, account_login):
        ''' История вывода средств пользователя account_login''' 
        data = AccountReports(Account(account_login)).money_out_requests()
        data.sort(key=lambda x:x['date'], reverse=True)
        
        return self.tableForDataMoneyOutRequest(data)
    
    @current_user_check 
    @expandtoken    
    @authcheck
    def moneyOutRemove(self):
        ''' Убирает заявку менеджера на вывод его средств'''
        try:
            id = int(request.params['id'])
            obj = app_globals.db.money_out_request.find({'user.login': c.manager_login}).sort('date')[id-1]

            if obj.get('approved', False):
                return h.JSON({'error': True, 'msg': u'Эта заявка уже была выполнена'})
            app_globals.db.money_out_request.remove(obj, safe=True)
        except:
            return h.JSON({'error': True, 'ok': False})

        return h.JSON({'error': False, 'ok': True, 'msg': 'Заявка успешно отменена'})    
    def openSchetFacturaFile(self):
        ''' Открывает файл счёт фактуры'''
        try:
            filename = request.params.get('filename')
            file = open('%s/%s' % (config.get('schet_factura_folder'), filename), 'rb')
        except:
            return u'Файл не найден!'
        
        content_type = {'.doc': 'application/msword',
                        '.docx': 'application/msword',
                        '.odt': 'application/msword',
                        '.rtf': 'application/msword',
                        '.pdf': 'application/pdf',
                        '.zip': 'application/zip',
                        '.odt': 'application/vnd.oasis.opendocument.text'}
        response.headers['Content-type'] = content_type.get(os.path.splitext(filename)[1], 'application/octet-stream')  
        return file
    
    def checkInformers(self, country='UA'):
        ''' Страница проверки работоспособности информеров в стране ``country`` '''

        def get_int(str):
            try:
                return int(re.findall("[0-9]+", str)[0])
            except:
                return 0
        
        c.informers = []
        for inf in app_globals.db.informer\
                           .find({}, ['guid', 'title', 'user', 'domain', 'admaker'])\
                           .sort('user'):
            try:
                width = get_int(inf['admaker']['Main']['width']) + 2 * get_int(inf['admaker']['Main']['borderWidth'])
                height = get_int(inf['admaker']['Main']['height']) + 2 * get_int(inf['admaker']['Main']['borderWidth'])
                valid = True
            except:
                width = height = 0
                valid = False
            c.informers.append({'guid': inf['guid'],
                                'title': inf['title'],
                                'user': str(inf['user']),
                                'domain': inf.get('domain'),
                                'width': width,
                                'height': height,
                                'valid': valid})
        c.country = country
        try:
            c.getmyad_worker_server = config['getmyad_worker_server']
        except KeyError:
            return 'В конфигурации не указан адрес сервера показа рекламы (см. ключ getmyad_worker_server)'
            
        return render('/informers.check.mako.html')
    
    
    def statcodeRequests(self):
        """Возвращает код статистики
        
        TODO: создать БД и вести учет отданных скриптов
        """
        url  = request.params['url']
        url = base64.urlsafe_b64encode(url)        
        code = """
<script type="text/javascript"><!--
var yottos_id = "%s";
//-->
</script>
<script type="text/javascript" src="http://getmyad.yottos.com.ua/js/yinfoe.js"></script>
        """ % url    
        db = pymongo.Connection("213.186.121.201")
        if code in db.stat.Domain.find({'code':url}):
            return code
        else:
            db.stat.Domain.update({'code':url},{'$set': {'script': code,'url':request.params['url'], 'user':'silver', 'date':datetime.now()}},upsert=True) 
        return code
    
    def statcodeDomains(self):
        db = pymongo.Connection("213.186.121.201").stat
        #db = app_globals.db.stat
        domains = []
        log.info(db.Domain.count())
        for item in db.Domain.find():     
            x = item['date']       
            domains.append({'url':item['url'],'date':str(x.year)+"."+str(x.month)+"."+str(x.day)})
            
        return json.dumps(domains)
        



class MoneyOutForm(formencode.Schema):
    """Форма вывода денег на web money"""
    allow_extra_fields = True
    filter_extra_fields = True
    moneyOut_summ = v.Number(min=10,
                             not_empty=True,
                             messages={'empty': u'Пожалуйста, введите сумму!',
                                       'number': u'Пожалуйста, введите корректную сумму!',
                                       'tooLow': u'Сумма должна быть не менее %(min)s $!'})
    moneyOut_comment = v.String(if_missing=None)
        
    
class updateUserForm(Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        
        edit_name = formencode.validators.String(not_empty=True, messages={'empty':u'Введите ФИО!'})
        edit_phone = formencode.validators.String(not_empty=True, messages={'empty':u'Введите телефон!'})
        edit_email = formencode.validators.Email(not_empty=True, messages={'empty':u'Введите e-mail!',
                                                                      'noAt': u'Неправильный формат e-mail!',
                                                                      'badUsername': u'Неправильный формат e-mail!',
                                                                      'badDomain': u'Неправильный формат e-mail!'})

    
