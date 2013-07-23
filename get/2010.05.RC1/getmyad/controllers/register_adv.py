# -*- coding: utf-8 -*-
import logging
import re
import pyodbc
from pymongo import Connection
from datetime import datetime
import sys
from optparse import OptionParser
import uuid
from urlparse import urlparse
from getmyad.lib import helpers as h
from getmyad.model import Account

from pylons import request, response, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect

from getmyad.lib.base import BaseController, render

log = logging.getLogger(__name__)

class RegisterAdvController(BaseController):

    def __init__(self):
        mongo_conn = Connection()
        self.mongo_db = mongo_conn.getmyad_db
        
        self.name = ''
        self.phone = ''
        self.email = ''
        self.site_url = ''
        self.error_messages = []
        self.login = ''
        self.password = ''
        self.minsum = ''
        self.manager_get = ''
        self.list_manager = []
        for x in self.mongo_db.users.find({'manager': True}):
            self.list_manager.append(x.get('login'))
        
#        connection_string = config.get("mssql_connection_string")
#        self.conn = pyodbc.connect(connection_string, autocommit=True)


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
        return render('/register_adv.mako.html',
                       extra_vars = {'errorMessage': '<br/>'.join(self.error_messages),
                                     'name': self.name,
                                     'phone': self.phone,
                                     'email': self.email,
                                     'site_url': self.site_url,
                                     'minsum': self.minsum,
                                     'manager_get': self.manager_get,
                                     'list_manager': self.list_manager})  
        


    def createUser(self):
        """Создаёт пользователя GetMyAd"""
        
        if not self.user: return h.userNotAuthorizedError()
        self.site_url = request.params.get('siteUrl')
        self.name = request.params.get('name')
        self.phone = request.params.get('phone')
        self.email = request.params.get('email')
        self.error_messages = []
        self.minsum = request.params.get('minsum')
        self.manager_get = request.params.get('manager_get')
        
        
        if not self.name or not self.site_url or not self.phone or not self.email:
            self.error_messages.append(u'Не заполнены необходимые поля!')

        if self.site_url:
            login_match = re.match(r'(?:http://)?(?:www\.)?([^/]+)', self.site_url)
            if not login_match:
                   self.error_messages.append(u'Неверный формат URL главной страницы сайта!')
            else:
                   self.login = login_match.group(1).lower()
                   if self.login and self.mongo_db.users.find_one({'login': self.login.lower()}):
                       self.error_messages.append(u'Сайт с таким URL уже зарегистрирован')    
                    
        if self.email:     
            if not re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", self.email):
                self.error_messages.append(u'Неверный e-mail!')
                
        
        if self.error_messages:
            return self.index()
         
        self.password = self._makePassword()
        
        session['login'] = self.login
        session['password'] = self.password
        session['name'] = self.name
        session['email'] = self.email
        session['phone'] = self.phone
        session['minsum'] = self.minsum
        session['manager_get'] = self.manager_get
        session.save()
        
        return render("/register.thanks.mako.html",
                      extra_vars = {'login': self.login,
                                    'password': self.password,
                                    'name': self.name,
                                    'email': self.email,
                                    'phone': self.phone,
                                    'minsum': self.minsum,
                                    'manager_get': self.manager_get,
                                    'list_manager': self.list_manager
                                    })
        
        
        
        
    def saveUser(self): 
        try:
            error_save = 0
            account = Account(login=session.get('login'))
            account.password = session.get('password')
            account.email = session.get('email')
            account.phone = session.get('phone')
            account.owner_name = session.get('name')
            account.min_out_sum = session.get('minsum')
            account.manager_get = session.get('manager_get')
            account.register()
            
            del session['login']
            del session['password']
            del session['email']
            del session['phone']
            del session['name']
            del session['minsum']
            del session['manager_get']
                
        except:
            error_save = 1    
        finally:
            return render("/register.thanks.mako.html",
                  extra_vars = {'login': account.login,
                                'password': account.password,
                                'name': account.owner_name,
                                'email': account.email,
                                'phone': account.phone,
                                'adv_created': 1,
                                'minsum': account.min_out_sum,
                                'manager_get': account.manager_get,
                                'error_save': error_save
                                 })


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
    
    
    
