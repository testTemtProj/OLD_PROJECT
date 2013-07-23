# -*- coding: utf-8 -*-
from datetime import datetime
from formencode import Schema
from getmyad.lib import helpers as h
from getmyad.lib.base import BaseController, render
from getmyad.model import Account
from optparse import OptionParser
from pylons import request, response, session, tmpl_context as c, url, config,\
    app_globals
from pylons.controllers.util import abort, redirect
from urlparse import urlparse
import logging
import re
import sys
import uuid
import formencode
from getmyad import model as model
from getmyad.model import Permission
#import pyodbc



log = logging.getLogger(__name__)

class RegisterAdvController(BaseController):

    def __init__(self):
        c.name = ''
        c.phone = ''
        c.email = ''
        c.siteUrl = ''
        c.user_error_messages = ''
        c.manager_error_messages = ''
        c.login = ''
        c.password = ''
        c.minsum = ''
        c.manager_get = ''
        c.list_manager = []
        c.manager_name = ''
        c.manager_login = ''
        c.manager_phone = ''
        c.manager_email = ''
        c.account_type = ''
        c.click_cost = 0.0
        c.money_web_z = False
        c.money_card = False
        c.money_factura = False
        for x in app_globals.db.users.find({'manager': True}):
            c.list_manager.append(x.get('login'))
        

    def __before__(self, action, **params):
        user = session.get('user')
        if user and session.get('isManager', False):
            self.user = user
            request.environ['CURRENT_USER'] = user
            request.environ['IS_MANAGER'] = True
        else:
            self.user = ''
     
    
    def index(self):
        if not self.user: return h.userNotAuthorizedError()
        permission = Permission(Account(login=self.user))
        if not permission.has(Permission.REGISTER_USERS_ACCOUNT):
            return h.userNotAuthorizedError()
        return render('/register_adv.mako.html')  

    class PaymentTypeNotDefined(Exception):
        ''' Не выбран ни один способ вывода средств '''
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return 'PaymentTypeNotDefined'
    
    def createUser(self):
        """Создаёт пользователя GetMyAd"""
        if not self.user: return h.userNotAuthorizedError()
        c.account_type = request.params.get('account_type', 'user')
        if c.account_type == 'user':
            schema = RegisterUserForm()
            try:
                form_result = schema.to_python(dict(request.params))
                c.name = form_result['name']
                c.phone = form_result['phone']
                c.email = form_result['email']
                c.siteUrl = form_result['siteUrl']
                c.minsum = request.params.get('minsum')
                c.click_cost = request.params.get('click_cost')
                c.manager_get = request.params.get('manager_get')
                c.money_card = False if request.params.get('money_card') == None else True
                c.money_web_z = False if request.params.get('money_web_z')  == None else True
                c.money_factura = False if request.params.get('money_factura') == None else True
                if (not c.money_card and not c.money_web_z and not c.money_factura):
                    raise RegisterAdvController.PaymentTypeNotDefined('Payment_type_not_defined')
            except formencode.Invalid, error:
                c.user_error_messages = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
                c.siteUrl = request.params.get('siteUrl')
                c.name = request.params.get('name')
                c.phone = request.params.get('phone')
                c.email = request.params.get('email')
                c.minsum = request.params.get('minsum')
                c.click_cost = request.params.get('click_cost')
                c.manager_get = request.params.get('manager_get')
                c.money_card = False if request.params.get('money_card') == None else True
                c.money_web_z = False if request.params.get('money_web_z')  == None else True
                c.money_factura = False if request.params.get('money_factura') == None else True 
                return self.index()
            except self.PaymentTypeNotDefined:
                c.user_error_messages = u'Укажите хотя бы один способ вывода средств'
                return self.index()
                
                
                
            
            c.siteUrl = request.params.get('siteUrl')
            if c.siteUrl.startswith('http://www.'):
                c.siteUrl = c.siteUrl[11:]
            elif c.siteUrl.startswith('http://'):
                c.siteUrl = c.siteUrl[7:]
            elif c.siteUrl.startswith('https://'):
                c.siteUrl = c.siteUrl[8:]    
            elif  c.siteUrl.startswith('www.'):
                c.siteUrl = c.siteUrl[4:]
            c.siteUrl = c.siteUrl.split('/')[0]
            
            c.money_out = ''
            if c.money_card:
                c.money_out += u'банковская платёжная карта'
            if c.money_web_z:
                if len(c.money_out):
                    c.money_out += ', '
                c.money_out += u'webmoney_z'
            if c.money_factura:
                if len(c.money_out):
                    c.money_out += ', '
                c.money_out += u'счёт фактура'    

        else:
            schema = RegisterManagerForm()
            try: 
                form_result = schema.to_python(dict(request.params))
                c.manager_login = form_result['manager_login']
                c.manager_name = form_result['manager_name']
                c.manager_email = form_result['manager_email']
                c.manager_phone = form_result['manager_phone']
            except formencode.Invalid, error:
                c.manager_error_messages = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
                c.manager_login = request.params.get('manager_login')
                c.manager_name = request.params.get('manager_name')
                c.manager_email = request.params.get('manager_email')
                c.manager_phone = request.params.get('manager_phone')    
                return self.index()

        c.user_error_messages = c.manager_error_messages = ''
        c.save_res = self.saveUser()
        return render("/register.thanks.mako.html")
        
        
        
        
    def saveUser(self):
        ''' Сохраняет создаваемый аккаунт в бд'''
        try:
            if c.account_type == 'user':
                account = Account(login=c.siteUrl)
                account.email = c.email
                account.phone = c.phone
                account.owner_name = c.name
                account.min_out_sum = c.minsum
                account.manager_get = c.manager_get
                account.money_web_z = c.money_web_z
                account.money_card = c.money_card
                account.money_factura = c.money_factura
            else:
                account = Account(login=c.manager_login)
                account.email = c.manager_email
                account.phone = c.manager_phone
                account.owner_name = c.manager_name
                    
            account.password = model.makePassword()
            c.password = account.password
            account.account_type = {'user': Account.User,
                                    'manager': Account.Manager,
                                    'admin': Account.Administrator
                                   }.get(c.account_type, Account.User)
            account.register()
            account.domains.add(account.login)
            model.setClickCost(float(c.click_cost), c.siteUrl, '', datetime.today())
        except:
            raise
            return 0
        return 1
        



    
    
    
class RegisterUserForm(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    siteUrl = formencode.validators.URL(not_empty=True, messages={'badURL': u'Неправильный формат URL',
                                                                  'empty':u'Введите URL'})
    name = formencode.validators.String(not_empty=True, messages={'empty':u'Введите ФИО'})
    phone = formencode.validators.String(not_empty=True, messages={'empty':u'Введите телефон'})
    click_cost = formencode.validators.Number(not_empty=True, messages={'empty': u'Введите цену за клик',
                                                                        'number': u'Некорректная цена за клик'})
    email = formencode.validators.Email(not_empty=True, messages={'empty':u'Введите e-mail',
                                                                  'noAt': u'Неправильный формат e-mail',
                                                                  'badUsername': u'Неправильный формат e-mail',
                                                                  'badDomain': u'Неправильный формат e-mail'})
    
    
class RegisterManagerForm(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    manager_login = formencode.validators.String(not_empty=True, messages={'empty':u'Введите логин'})
    manager_name = formencode.validators.String(not_empty=True, messages={'empty':u'Введите ФИО'})
    manager_phone = formencode.validators.String(not_empty=True, messages={'empty':u'Введите телефон'})
    manager_email = formencode.validators.Email(not_empty=True, messages={'empty':u'Введите e-mail'})    

    

