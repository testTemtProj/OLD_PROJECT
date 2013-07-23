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
            c.user = user
            request.environ['CURRENT_USER'] = user
            request.environ['IS_MANAGER'] = True
        else:
            c.user = ''


    def index(self):
        """Кабинет менеджера"""
        if not c.user: 
            return redirect('/')
        
        token = str(uuid1()).upper()
        session[token] = {'user': session.get('user')}
        session.save()
        c.token = token      
        
        c.domainsRequests = self.domainsRequests()
        c.dataMoneyOutRequests = self.dataMoneyOutRequests()
        c.managersSummary = self.managersSummary()
        c.dataOverallSummary = self.overallSummaryByDays()
        c.account = model.Account(login=c.user)
        c.account.load()
        c.permission = Permission(c.account)
        c.date = self.todayDateString()
        c.acc_count = len(self._usersList())
        c.sum_out = self.sumOut() 
        c.prognoz_sum_out = '%.2f $' % self.prognozSumOut()
        
        c.active_counters = self.activeAccountsAndDomainsCount()
        c.notApprovedRequests = self.notApprovedActiveMoneyOutRequests()
        c.moneyOutHistory = self.moneyOutHistory()
        c.dataUsersImpressions = self.dataUsersImpressions()
        c.usersSummaryActualTime = self.usersSummaryActualTime()
        log.info('Loggin user: %s ', c.user)
        
        return render("/manager.mako.html",
                      extra_vars={ 'dataUsersSummary': self.dataUsersSummary()})
        
        
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
           
    def activeAccountsAndDomainsCount(self):
        '''Кол-во активных аккаунтов и сайтов сегодня и в предыдущие дни'''
        act_acc_count = 0
        yest_act_acc_count = 0
        b_yest_act_acc_count = 0
        domains_today = domains_yday = domains_byday = 0
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
                active_domains = x.get('active_domains', {})
                domains_today += active_domains.get('today', 0)
                domains_yday += active_domains.get('yesterday', 0)
                domains_byday += active_domains.get('before_yesterday', 0)
            except KeyError:
                pass
        return {'accounts': {'today': act_acc_count,
                             'yesterday': yest_act_acc_count,
                             'before_yesterday': b_yest_act_acc_count},
                'domains':  {'today': domains_today,
                             'yesterday': domains_yday,
                             'before_yesterday': domains_byday} }
        
    def managersSummary(self):
        ''' Данные для таблицы данных о менеджерах'''
        ''' TODO в бд в поле blocked надо привести в единый вид и описать значения полей '''
        db = app_globals.db
        data = []
        for manager in db.users.find({"accountType": {'$in': ['manager', 'administrator']}}):
            if manager['accountType'] == 'manager':
                balance = model.ManagerReports(Account(manager['login'])).balance()
            else:
                balance = 0.0
            data.append((manager['login'], manager.get('percent', 0), "%.2f" % balance, manager.get('blocked', ''), manager['accountType']))
        return h.jgridDataWrapper(data)
    
    @current_user_check 
#    @expandtoken    
#    @authcheck    
    def overallSummaryByDays(self):
        ''' Данные для таблицы суммарных данных по дням ("Общая статистика") '''
        data = []
        for x in app_globals.db.stats_overall_by_date.find().sort('date', pymongo.DESCENDING):
            ctr = 100.0 * x['clicksUnique'] / x['impressions'] if x.get('impressions', False) else 0
            click_cost_avg = x['totalCost'] / x['clicksUnique'] if x.get('clicksUnique', False) else 0
            AccountSiteCount = str(x.get('act_acc_count', 0)) + "/" + str(x.get('domains_today', 0))
            row = (x['date'].strftime("%d.%m.%Y"),
                   AccountSiteCount,
                   int(x.get('impressions', 0)),
                   int(x.get('clicks', 0)),
                   int(x.get('clicksUnique', 0)),
                   h.formatMoney(x.get('totalCost', 0)),
                   '%.3f' % ctr,
                   '%.2f ¢' % (click_cost_avg * 100)
                   )
            data.append(row)
        return h.jqGridLocalData(data,
                                 ['date', 'AccountSiteCount', 'impressions', 'clicks',
                                  'clicksUnique', 'profit', 'ctr',
                                  'click_cost'])
    
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
            return h.JSON({'error': True, 'msg': 'invalid arguments', 
                           'ok': False})
        model.setManagerPercent(manager_login, percent)
        return h.JSON({'error': False, 'ok': True})


    @current_user_check 
    @expandtoken    
    @authcheck    
    def block(self):
        """ Блокирует менеджера, логин которого передаётся в GET-параметре 
            ``manager`` """
        try:
            manager_login = request.params['manager']
            manager = model.Account(manager_login)
            manager.load()
            manager.blocked = 'banned'
            manager.update()
        except:
            return h.JSON({'error': True, 'ok': False})
        else:
            return h.JSON({'error': False, 'ok': True})

    
    @current_user_check 
    @expandtoken    
    @authcheck    
    def setClickCost(self):
        """ Устанавливает цену за клик для пользователя.
            
            Принимает следующие GET-параметры:

            ``user``
                пользователь, которому назначается цена.

            ``type``
                типа расчёта цены. Может принимать два значения:

                1. ``fixed_cost`` -- за каждый клик пользователю будет
                   начисляться фиксированная сумма, указанная в параметре
                   ``cost``.

                2. ``percent`` -- пользователю будет начисляться процент от
                   стоимости, которую рекламодатель заплатит за клик. В этом
                   случае будут использованы параметры ``percent``, ``min`` и
                   ``max``.

            ``cost``
                фиксированная цена за клик.

            ``percent``
                процент от суммы, заплаченной рекламодателем.

            ``min``
                минимальная цена, ниже которой не могут опускаться отчисления,
                независимо от процента и цены рекламодателя.

                Если параметр равен пустой строке или отсутствует, то он 
                считается не заданным и цена не будет иметь нижней границы.

            ``max``
                максимальная цена, выше которой не могут подниматься отчисления,
                независимо от процента и цены рекламодателя.

                Если параметр равен пустой строке или отсутствует, то он 
                считается не заданным и цена не будет иметь верхней границы.

            ``date``
                время/дата, начиная с которого вступает в действие цена.
        """
        if not Permission(Account(c.user)).has(Permission.SET_CLICK_COST):
            return h.insufficientRightsError()
        try:
            user = request.params['user']
            date = h.datetimeFromStr(request.params['date'])
            payment_type = request.params.get('type')
            if payment_type not in ['fixed_cost', 'percent']:
                payment_type = 'fixed_cost'

            if payment_type == 'percent':
                # Плавающая цена за клик
                percent = float(request.params['percent'])
                try:
                    cost_min = float(request.params['min'])
                except (ValueError, KeyError):
                    cost_min = None
                try:
                    cost_max = float(request.params['max'])
                except (ValueError, KeyError):
                    cost_max = None
                model.setFloatingCostForClick(user, date, percent,
                                              cost_min, cost_max)
            else:
                # Фиксированная цена за клик
                cost = float(request.params['cost'])
                model.setFixedCostForClick(user, cost, date)
        except (ValueError, KeyError):
            return h.JSON({'error': True, 'ok': False,
                           'msg': 'invalid arguments'})
        else:
            return h.JSON({'error': False, 'ok': True})

    
    def currentClickCost(self):
        """ Возвращает данные для таблицы текущих цен за уникального посетителя.
            
            Принимает следующие GET-параметры:
            
            onlyActive
                Если ``true``, то возвращает цены только для активных аккаунтов.
                По умолчанию равен ``false``.

            sidx
                Наименование колонка, по которой проводить сортировку.

            sord
                Порядок сортировки, ``asc`` или ``desc``.
                
            Формат возвращаемых данных: JSON для таблицы jqGrid со следующими
            столбцами:

            1. Логин пользователя.
            2. Цена за клик (строкой).
            3. Время/дата начала действия цены.
            4. Процент от цены рекламодателя (скрытая колонка).
            5. Минимальная цена (скрытая колонка).
            6. Максимальная цена (скрытая колонка).

        """
        if not c.user:
            return h.userNotAuthorizedError()
        costs = list(model.currentClickCost())
        users = self._usersList()
        filter_inactive = request.params.get('onlyActive', 'false') == 'true'
        if filter_inactive:
            active_users = [x.get('login') for x in
                                app_globals.db.user.summary_per_date.find(
                                    {'activity': 'greenflag'})]
            users = set(users).intersection(set(active_users))
        
        data = []
        sum_fixed_cost = 0      # для вычисления средней цены
        count_fixed_costs = 0   #   за клик
        for cost in costs:
            user = cost['user_login']
            if user not in users:
                continue
            if cost['date']:
                date_str = cost['date'].strftime("%d.%m.%Y %H:%M") 
            else:
                date_str = ''
            if cost['type'] == 'fixed':
                cost_str = "%.2f" % cost['cost']
                sum_fixed_cost += cost['cost']
                count_fixed_costs += 1
                percent = ''
                cost_min = ''
                cost_max = ''
            else:
                cost_str = u'%s%%' % int(cost['percent'])
                if cost['min']:
                    cost_str += u', от %s¢' % int(cost['min'] * 100)
                if cost['max']:
                    cost_str += u' до %s¢' % int(cost['max'] * 100)
                percent = round(cost['percent'], 0)
                try:
                    cost_min = round(cost['min'], 2)
                except (TypeError, ValueError):
                    cost_min = 0
                try:
                    cost_max = round(cost['max'], 2)
                except (TypeError, ValueError):
                    cost_max = 1.0

            data.append((user, cost_str, date_str, percent, cost_min, cost_max))

        try:    
            avg_cost = float(sum_fixed_cost) / count_fixed_costs
        except ZeroDivisionError:
            avg_cost = 0
        finally:    
            userdata = {'user': u'Средняя цена за клик',
                        'cost': "%.3f" % avg_cost,
                        'day' : ''}
        # Сортировка
        try:
            sort_col = request.params['sidx']
            sort_index = ['user', 'cost', 'date'].index(sort_col)
            reverse = request.params.get('sord') == 'desc'
            data.sort(key=lambda x: x[sort_index], reverse=reverse)
        except (KeyError, ValueError):
            pass

        return h.jgridDataWrapper(data, userdata)


    def prognozSumOut(self):
        'Возвращает прогнозируемую сумму к выводу на ближайшее 10-е число'
        today = datetime.today()
        one_month = timedelta(days=30)
        if today.day > 10:
            month_day_10 = today + one_month
            month_day_10 = datetime(month_day_10.year, month_day_10.month, 10)
        else:
            month_day_10 = datetime(today.year, today.month, 10)
        daysdelta = month_day_10 - today

#        users = self._usersList()
        calc_sum_out = 0
        for x in app_globals.db.user.summary_per_date.find():
            try:
                avg_day_sum = float(x['income']['week']) / 7
            except KeyError:
                avg_day_sum = 0
            account_delta = avg_day_sum * daysdelta.days
            account_sum = account_delta + x.get('summ', 0.0)
            try:
                data = app_globals.db.users.find_one({'login': x['login']})
                min_out_sum = float(data['min_out_sum'])
                prepayment = data.get('prepayment', False)
            except:
                min_out_sum = 100
                prepayment = False
            if account_sum >= min_out_sum or prepayment:
                calc_sum_out += account_sum
            
        return calc_sum_out


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
                prepayment = user_data.get('prepayment', False)
            except (KeyError, ValueError, TypeError):
                min_out_sum = 100
                prepayment = False

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
            if prepayment or accountSumm >= min_out_sum:
                result[payment_type] += accountSumm
                result['total'] += accountSumm
                
        return result
    
    
    def tableForDataMoneyOutRequest(self, data_from_db):
        '''Возвращает форматированные данные для jgrid.

           На входе принимает результат запроса к db.money_out_request.

           Обращает внимание на get-параметры ``page`` и ``rows``, 
           которые нужны jqGrid для пейджинга.
           '''
        
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
        
        if not c.user: return h.userNotAuthorizedError()
        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
            return h.JSON(None)
        data = []
        for x in data_from_db:
            login = x['user']['login']
            date = x.get('date').strftime("%d.%m.%Y %H:%M")
            summ = '%.2f $' % x['summ']
            user_confirmed = u"Да" if x.get('user_confirmed') else u"Нет"    
            approved = u"Да" if x.get('approved', False) \
                             else u"<b style='color: red;'>Нет</b>"    
            manager_agreed = u"Да" if x.get('manager_agreed', False) \
                                   else u"<b style='color: red;'>Нет</b>"    
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
            elif x.get('paymentType') == 'yandex':
                comment = (u'<b>Счёт Яндекс Деньги:</b> %s<br/>')% x['yandex_number']

            else:
                comment = u''                         

            if x.get('ip'):
                comment += u'<b>IP:</b> %s <br />' % x['ip']
            
            if x.get('comment'):
                comment += u'<b>Примечания:</b> %s ' % commentFormat(x['comment'])               

            protectionCode = x.get('protectionCode', '')
            protectionDate = x.get('protectionDate', '')
            protectionDate = protectionDate.strftime("%d.%m.%Y") if isinstance(protectionDate, datetime) else ''
            
            data.append((login, date, summ, user_confirmed, manager_agreed, 
                         approved, phone, paymentType, protectionCode, protectionDate, comment))                
        return h.jgridDataWrapper(data, 
                                  page=request.params.get('page', 1),
                                  records_on_page=request.params.get('rows', 10))
        

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
        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
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
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        protectionCode = request.params.get('protectionCode', '')
        protectionPeriod = request.params.get('protectionPeriod', '')

        if len(protectionCode) and not protectionCode.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        if len(protectionPeriod) and not protectionPeriod.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        # Обновляем заявку
        db = app_globals.db
        money_out_request = \
            db.money_out_request.find_one({'user.login': user,
                                           'date': {'$gte': date,
                                                    '$lte': (date + timedelta(seconds=60))}})
        money_out_request['approved'] = approved
        money_out_request['protectionCode'] = protectionCode
        money_out_request['protectionDate'] = datetime.now() + timedelta(days=int(protectionPeriod)) if len(protectionPeriod) else ''
        db.money_out_request.save(money_out_request, safe=True)
        
        # Обновляем последний метод вывода средств для пользователя 
        db.users.update({'login': user},
                        {'$set': {'lastPaymentType': money_out_request.get('paymentType', '')}},
                        safe=True)

        return json.dumps({'error': False, 'ok': True, 'date': date.strftime("%d.%m.%Y %H:%M"), 'date2': (date + timedelta(seconds=60)).strftime("%d.%m.%Y %H:%M")})


    @current_user_check 
    @expandtoken    
    @authcheck 
    def agreeMoneyOut(self):
        """ Разрешает заявку пользователя ``user`` со временем ``date``
            (передаются в GET-параметрах) """

        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
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
            return json.dumps({'error': True, 'msg': 'invalid arguments', 
                               'ok': False})

        # Обновляем заявку
        db = app_globals.db
        money_out_request = \
            db.money_out_request.find_one({'user.login': user,
                                           'date': {'$gte': date,
                                                    '$lte': (date + timedelta(seconds=60))}})
        money_out_request['manager_agreed'] = approved
        db.money_out_request.save(money_out_request, safe=True)
        
        return h.JSON({'error': False, 'ok': True,
                       'date': date.strftime("%d.%m.%Y %H:%M"),
                       'date2': (date + timedelta(seconds=60))\
                                        .strftime("%d.%m.%Y %H:%M")})


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
                link_class = "actionLink %s" % x['activity']
                if self._is_yellow_star(x):
                    link_class += " yellow_star"
                data.append(('<a href="javascript:;" class="%s" >%s</a>'%(link_class,x['login']),
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

    def _is_yellow_star(self, user_summary):
        """Возвращает True, если пользователь подключился в течении последних
        суток. Такие пользователи подсвечиваются жёлтой звездочкой.

        Поскольку точно расчитать активность пользователя за последние 24 часа
        не возможно, применяется следующий алгоритм:

        1. Если текущее время меньше 12 часов, смотрим активность за текущий и
           два последних календарных дня.

        2. Если текущее время больше 12 часов, смотрим активность за текущий и
           вчерашний календарный день.

        ``user_summary``
            Структура из коллекции ``user.summary_per_date``.
        """
        now = datetime.now()
        active_today = user_summary.get('activity') == 'greenflag'
        active_yday = user_summary.get('activity_yesterday') == 'greenflag'
        active_before_yday = user_summary.get('activity_before_yesterday') == 'greenflag'

        if now.hour < 12:
            result = (active_today or active_yday) and not active_before_yday

        else:
            result = active_today and not active_yday

        return result


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
        sumWeekCTR = 0

        for x in app_globals.db.user.summary_per_date.find().sort('registrationDate'):
            if x['login'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"
            data.append(('<a href="javascript:;" class="%s" >%s</a>' % 
                                                (link_class, x['login']),
                        h.formatMoney(x['income']['today']),
                        h.formatMoney(x['income']['yesterday']),
                        h.formatMoney(x['income']['before_yesterday']),
                        h.formatMoney(x['income']['week']),
                        h.formatMoney(x['income']['month']),
                        h.formatMoney(x['income']['year']),
                        '%.3f' % x['day_CTR'],
                        '%.3f' % x.get('week_CTR', 0),
                        h.formatMoney(x['summ']),
                        2 if x['activity'] == "greenflag" else 1))
            if x['summ'] >= 0:
                totalSumm += x['summ']
            else: 
                totalSummMinus += x['summ'] * (-1)    
            totalSummToday += x['income']['today']
            totalSummYesterday += x['income']['yesterday']
            totalSummBeforeYesterday += x['income']['before_yesterday'] 
            totalSummWeek += x['income']['week']
            totalSummMonth += x['income']['month']
            totalSummYear += x['income']['year']
            sumDayCTR += x['day_CTR']
            sumWeekCTR += x.get('week_CTR', 0)

        try:            
            totalDayCTR = float(sumDayCTR) / float(len(users))
            totalWeekCTR = float(sumWeekCTR) / float(len(users))
            totalDayCTR = '%.3f' % totalDayCTR 
            totalWeekCTR = '%.3f' % totalWeekCTR 
        except ZeroDivisionError:
            totalDayCTR = totalWeekCTR = ''  
            
        userdata = {'user': u'ИТОГО:',
                    'summ': h.formatMoney(totalSumm) + ", -" + h.formatMoney(totalSummMinus),
                    'summToday': h.formatMoney(totalSummToday),
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'summBeforeYesterday': h.formatMoney(totalSummBeforeYesterday),
                    'summWeek': h.formatMoney(totalSummWeek),
                    'summMonth': h.formatMoney(totalSummMonth),
                    'summYear': h.formatMoney(totalSummYear),
                    'dayCTR': totalDayCTR,
                    'weekCTR': totalWeekCTR
                   }

        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
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
        if not c.user: return h.userNotAuthorizedError()
        if not Permission(Account(c.user)).has(Permission.USER_DOMAINS_MODERATION): return h.jgridDataWrapper([])
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
        if not Permission(Account(c.user)).has(Permission.VIEW_MONEY_OUT): return h.insufficientRightsError() 
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
        if not Permission(Account(c.user)).has(Permission.VIEW_MONEY_OUT): return h.insufficientRightsError() 
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
        if not c.user: return []
        users_condition = {'manager': {'$ne' : True}}
        if not Permission(Account(login=c.user)).has(Permission.VIEW_ALL_USERS_STATS):
            users_condition.update({'managerGet': c.user})
        users = [x['login'] for x in app_globals.db.users.find(users_condition).sort('registrationDate')]
        return users
    
    
    @current_user_check
    def userDetails(self):
        """ Вкладка детальной информации о пользователе """
        c.permission = Permission(Account(login=c.user))
        c.login = request.params.get('login')
        c.token = request.params.get('token')
        c.div_to_open = h.JSON(request.params.get('div'))
        if not c.login:
            return h.JSON({"error": True, 'msg': u'Неверно указаны параметры',
                           'ok': False})
        edit_account = model.Account(c.login)
        edit_account.load()
        c.edit_min_out_sum = edit_account.min_out_sum
        c.edit_manager_get = edit_account.manager_get
        c.list_manager = model.active_managers()
        c.edit_name = edit_account.owner_name
        c.edit_phone = edit_account.phone
        c.edit_email = edit_account.email
        c.edit_money_web_z = 'webmoney_z' in edit_account.money_out_paymentType
        c.edit_money_card = 'card' in edit_account.money_out_paymentType
        c.edit_money_factura = 'factura' in edit_account.money_out_paymentType
        c.edit_money_yandex = 'yandex' in edit_account.money_out_paymentType
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
        return render("administrator/user-details.mako.html")

    def userDomainDetails(self):
        ''' Таблица статистики по доменам пользователя.
        
            Логин пользователя передаётся в GET-параметре ``user``.
        '''
        user = request.params.get('user')
        db = app_globals.db
        domain_by_informer = {}
        informers_id = []
        for i in db.informer.find({'user': user}):
            domain_by_informer[i['guid']] = i.get('domain', '')
            informers_id.append(i['guid'])
        date_start = h.trim_time(datetime.today() - timedelta(days=300))
        data_by_date_and_domain = {}
        for x in db.stats_daily_adv.find({'adv': {'$in': informers_id},
                                          'date': {'$gte': date_start}}):
            domain = domain_by_informer.get(x['adv'], '')
            key = (x['date'], domain)
            record = data_by_date_and_domain \
                         .setdefault(key, {'clicks': 0,
                                           'unique': 0,
                                           'imp': 0,
                                           'summ': 0})
            record['clicks'] += x.get('clicks', 0)
            record['unique'] += x.get('clicksUnique', 0)
            record['imp'] += x.get('impressions', 0)
            record['summ'] += x.get('totalCost', 0)

        # Сортировка
        raw_data = data_by_date_and_domain.items()
        reverse = request.params.get('sord') == 'desc'
        sidx = request.params.get('sidx')
        if not sidx:
            # Параметры по умолчанию
            sidx = 'date'
            reverse = True

        if sidx == 'date':
            # сначала по дате, затем по домену
            sfunc = lambda x: '%s %s' % (x[0][0].strftime('%Y%m%d'), x[0][1])
        else:
            # сначала по домену, затем по дате
            sfunc = lambda x: '%s %s' % (x[0][1], x[0][0].strftime('%Y%m%d'))

        raw_data.sort(key=sfunc, reverse=reverse)
 
        # Форматируем вывод в таблицу
        data = []
        for k, v in raw_data:
            date, domain = k
            if v['imp']:
                ctr = v['unique'] * 100.0 / v['imp']
            else:
                ctr = 0
            data.append((date.strftime("%d.%m.%Y"),
                         domain, v['clicks'], v['unique'],
                         v['imp'],
                         '%.3f' % ctr,
                         '%.2f' % v['summ']))

        return h.jgridDataWrapper(data)
        



    
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
        edit_account.money_yandex = False if not request.params.get('edit_money_yandex') else True
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
        extension = os.path.splitext(filename)[1].lower()
        response.headers['Content-type'] = \
            content_type.get(extension, 'application/octet-stream')  
        return file
    
    def checkInformers(self, country):
        ''' Страница проверки работоспособности информеров в стране ``country`` '''
        user = request.environ.get('CURRENT_USER') or session.get('adload_user')
        if not user:
            return h.userNotAuthorizedError()

        region = request.params.get('region', '')

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
        c.all_geo_regions = [(x['region'], x.get('ru')) for x in app_globals.db.geo.regions.find({'country': c.country}).sort('ru')]
        c.all_geo_regions.insert(0, ('', u'(любая область)'))
        c.selected_region = region
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
<script type="text/javascript" src="http://cdn.yottos.com/getmyad/yinfoe.js"></script>
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

    @current_user_check 
    @expandtoken    
    @authcheck 
    def updateProtection(self):
        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
            return h.insufficientRightsError()

        user = request.params.get('user', None)
        date = h.datetimeFromStr(request.params.get('date'))

        if not user or not date:
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        protectionCode = request.params.get('protectionCode', '')
        protectionPeriod = request.params.get('protectionPeriod', '')

        if len(protectionCode) and not protectionCode.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        if len(protectionPeriod) and not protectionPeriod.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        db = app_globals.db

        money_out_request = \
            db.money_out_request.find_one({'user.login': user,
                                           'date': {'$gte': date,
                                                    '$lte': (date + timedelta(seconds=60))}})

        money_out_request['protectionCode'] = protectionCode
        money_out_request['protectionDate'] = datetime.now() + timedelta(days=int(protectionPeriod)) if len(protectionPeriod) else ''
        db.money_out_request.save(money_out_request, safe=True)
        
        return h.JSON({'error': False, 'ok': True,
                       'date': date.strftime("%d.%m.%Y %H:%M"),
                       'date2': (date + timedelta(seconds=60))\
                                        .strftime("%d.%m.%Y %H:%M")})



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

    
