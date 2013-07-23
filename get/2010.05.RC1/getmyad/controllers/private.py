# -*- coding: utf-8 -*-
import logging
import formencode
from formencode import htmlfill

from pylons import request, response, session, tmpl_context as c, url,\
    app_globals
from pylons.controllers.util import abort, redirect

from getmyad.lib.base import BaseController, render
from routes.util import redirect_to
from getmyad.controllers.advertise import AdvertiseController
import json
import pymongo.json_util
from getmyad.lib import helpers as h
from datetime import datetime
import getmyad
from getmyad import model
from getmyad.model import AccountReports, Account

log = logging.getLogger(__name__)

class PrivateController(BaseController):
    
    def __before__(self, action, **params):
        user = session.get('user')
        if user:
            request.environ['CURRENT_USER'] = user
            request.environ['IS_MANAGER'] = session.get('isManager', False)

    def index(self):
        """Основная страница статистики (кабинет пользователя) """ 
        user = request.environ.get('CURRENT_USER')
        if not user:
            return redirect(url(controller='main', action='index'))
        if request.environ['IS_MANAGER']:
            return redirect(url(controller='manager', action='index'))
         
        try:
            data = app_globals.db.users.find_one({'login': user})
            min_out_sum = float(data['min_out_sum'])
        except:
            min_out_sum = 100    
            
        account = model.Account(user)
        ad = AdvertiseController()
        c.updateTime = model.updateTime()
        c.chartData = ad.days()
        c.summaryReportData = ad.allAdvertises()
        c.accountSumm = account.report.balance()
        c.informers = account.informers()
        c.moneyOutEnabled = (c.accountSumm >= min_out_sum)
        c.moneyOutHistory = self.moneyOutHistory()
        c.min_out_sum = min_out_sum
        c.domains = account.domains()

        return render('/statistics.mako.html')
    
        
    def accountIncome(self):
        """Возвращает данные о начислении денег на счёт"""
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        
        ads = [x.guid for x in model.Account(user).informers()]
        db = app_globals.db
        data = db.stats_daily_adv.group(['date'],
                                        {'adv': {'$in': ads}},
                                        {'sum': 0, 'unique': 0},
                                        'function(o,p) {p.sum += o.totalCost || 0; p.unique += o.clicksUnique || 0; }')
        data.sort(key=lambda x:x['date'])
        data.reverse()
        return h.jgridDataWrapper([(x['date'].strftime("%d.%m.%Y"),
                                    x['unique'],
                                    '%.2f $' % (x['sum'] / x['unique']) if x['unique'] else 0,
                                    '%.2f $' % x['sum']
                                    ) for x in data])
    
    
    def moneyOutHistory(self):
        """История вывода денег""" 
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()

        data = AccountReports(Account(user)).money_out_requests()
        data.sort(key=lambda x:x['date'])
        
#        data = app_globals.db.money_out_request.find({'user.login': user})
#        data.sort('date', pymongo.ASCENDING)
        
        table = [(x['date'].strftime("%d.%m.%Y"),
                  x['paymentType'],
                  '%.2f $' % x['summ'],
                  x.get('comment') if x.get('approved') else u'заявка обрабатывается...')
                 for x in data]
        return h.jgridDataWrapper(table)
        
    
    
    def moneyOutSubmit(self):
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        
        schema = MoneyOutForm()
        try:
            form = schema.to_python(dict(request.params))
        except formencode.Invalid, error:
            errorMessage = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
            return json.dumps({'error': errorMessage, 'ok': False}, ensure_ascii=False)
        
        app_globals.db.money_out_request.insert(
                    {
                         'date': datetime.now(),
                         'user': {'guid': '',
                                  'login': user},
                         'summ': form.get('moneyOut_summ'),
                         'paymentType': 'webmoney_z',
                         'webmoneyLogin': form.get('moneyOut_webmoneyLogin'),
                         'webmoneyAccount': form.get('moneyOut_webmoneyAccountNumber'),
                         'phone': form.get('moneyOut_phone'),
                         'comment': form.get('moneyOut_comment')
                    })
        return json.dumps({'error': None, 'ok': True, 'msg': 'Заявка успешно принята'})
    #def 
       
        
        
        
        
        
        
        
class MoneyOutForm(formencode.Schema):
    """Форма вывода денег"""
    allow_extra_fields = True
    filter_extra_fields = True
    moneyOut_summ = formencode.validators.Number(min=10, not_empty=True,
                                                 messages={'empty': u'Пожалуйста, введите сумму!',
                                                           'number': u'Пожалуйста, введите корректную сумму!',
                                                           'tooLow': u'Сумма должна быть не менее %(min)s $!'})
    moneyOut_webmoneyLogin = formencode.validators.NotEmpty(messages={
                                                                      'empty': u'Пожалуйста, введите логин WebMoney!'})
    moneyOut_webmoneyAccountNumber = formencode.validators.NotEmpty(messages={
                                                                              'empty': u'Пожалуйста, введите номер кошелька WebMoney!'})
    moneyOut_phone = formencode.validators.NotEmpty(messages={
                                                              'empty': u'Пожалуйста, введите номер телефона!'})
    moneyOut_comment = formencode.validators.String(if_missing=None)