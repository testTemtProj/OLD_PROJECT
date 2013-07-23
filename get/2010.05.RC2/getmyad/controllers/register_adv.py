# -*- coding: utf-8 -*-
from datetime import datetime
from formencode import Schema
from getmyad.lib import helpers as h
from getmyad.lib.base import BaseController, render
from getmyad.model import Account
from optparse import OptionParser
from pylons import request, response, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect
from pymongo import Connection
from urlparse import urlparse
import logging
import re
import sys
import uuid
import formencode
#import pyodbc



log = logging.getLogger(__name__)

class RegisterAdvController(BaseController):

    def __init__(self):
        mongo_conn = Connection()
        c.mongo_db = mongo_conn.getmyad_db
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
        for x in c.mongo_db.users.find({'manager': True}):
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
        return render('/register_adv.mako.html')  
        


            
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
                c.minsum = form.minsum
                c.manager_get = form.manager_get

            except formencode.Invalid, error:
                c.user_error_messages = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
                c.siteUrl = request.params.get('siteUrl')
                c.name = request.params.get('name')
                c.phone = request.params.get('phone')
                c.email = request.params.get('email')
                c.minsum = request.params.get('minsum')
                c.manager_get = request.params.get('manager_get')
                return self.index()
            
            c.siteUrl = request.params.get('siteUrl')
            c.name = request.params.get('name')
            c.phone = request.params.get('phone')
            c.email = request.params.get('email')
            c.minsum = request.params.get('minsum')
            c.manager_get = request.params.get('manager_get')

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
        try:
            if c.account_type == 'user':
                account = Account(login=c.login)
                account.email = c.email
                account.phone = c.phone
                account.owner_name = c.name
                account.minsum = c.minsum
                account.manager_get = c.manager_get
            else:
                account = Account(login=c.manager_login)
                account.email = c.manager_email
                account.phone = c.manager_phone
                account.owner_name = c.manager_name
                    
            account.password = self._makePassword()
            c.password = account.password
            account.account_type = {'user': Account.User,
                                    'manager': Account.Manager,
                                    'admin': Account.Administrator
                                   }.get(c.account_type, Account.User)
            account.register()
            account.domains.add(account.login)
        except:
            return 0
        else:
            return 1
        


    def _makePassword(self):
        """Возвращает сгенерированный пароль"""
        from random import Random
        rng = Random()
    
        righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
        lefthand = '789yuiophjknmYUIPHJKLNM'
        allchars = righthand + lefthand
        
        passwordLength = 8
        alternate_hands = True
        password = ''
        
        for i in range(passwordLength):
            if not alternate_hands:
                password += rng.choice(allchars)
            else:
                if i % 2:
                    password += rng.choice(lefthand)
                else:
                    password += rng.choice(righthand)
        return password
    
    
    
class RegisterUserForm(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    siteUrl = formencode.validators.URL(not_empty=True, messages={'badURL': u'Неправильный формат URL',
                                                                  'empty':u'Введите URL'})
    name = formencode.validators.String(not_empty=True, messages={'empty':u'Введите ФИО'})
    phone = formencode.validators.String(not_empty=True, messages={'empty':u'Введите телефон'})
    email = formencode.validators.Email(not_empty=True, messages={'empty':u'Введите e-mail'})
    
class RegisterManagerForm(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    manager_login = formencode.validators.String(not_empty=True, messages={'empty':u'Введите логин'})
    manager_name = formencode.validators.String(not_empty=True, messages={'empty':u'Введите ФИО'})
    manager_phone = formencode.validators.String(not_empty=True, messages={'empty':u'Введите телефон'})
    manager_email = formencode.validators.Email(not_empty=True, messages={'empty':u'Введите e-mail'})    

    

