# -*- coding: utf-8 -*-
from datetime import datetime
from getmyad.lib.base import BaseController, render
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals
from pylons.controllers.util import abort, redirect
import logging
#from paste.httpserver import protocol

log = logging.getLogger(__name__)

class MainController(BaseController):

    def index(self):
        c.Comment=True        
        if session.get('user'):
       
            if not session.get('isManager', False):
                return redirect(url(controller='private', action='index'))
            else:
                return redirect(url(controller='manager', action='index'))
        
        errorMessage = session.get('error_message')
        if errorMessage:
            del session['error_message']
            session.save()
        #return redirect(url(controller="register_adv", action="index"))
        return render('/index.mako.html', extra_vars = 
                      {'errorMessage': errorMessage})

    def signIn(self):
        """Вход пользователя. Должны передаваться параметры login и password"""
        c.Comment=False 
        login = request.POST.get("login")
        password = request.POST.get('password')
        user = app_globals.db.users.find_one({'login': login,
                                              'password': password})
        if user <> None:
            blocked = user.get('blocked', False)
            if blocked == 'banned':
                session['error_message'] = u'Аккаунт заблокирован'
                session.save()
                return self.signOut()
            if blocked == 'light':
                c.login = login
                return render('/user/account_blocked.mako.html')
            
            session['user'] = user['login']
            session['isManager'] = user.get('manager', False)
            session.save()
            if not session['isManager']:
                c.redirect_url = '/private/index'
                return render("/loading.mako.html")
#                return redirect(url(controller="private", action="index"), code=303)
            else:
                c.redirect_url = '/manager/index'
                c.manager = True
                return render("/loading.mako.html")
#                return redirect(url(controller="manager", action="index"), code=303)
        else:
            session['error_message'] = u'Неверный логин или пароль!'
            session.save()
            self.signOut()


    def signOut(self):
        """Выход пользователя"""
        c.Comment=False 
        # записываем в бд время выхода из аккаунта
        app_globals.db.users.update({'login' : session.get('user')}, {'$set': {'signOutTime': datetime.today()}})
        
        if 'user' in session:
            del session['user']
        session.save()
        return redirect(url(controller="main", action="index"))


    def signUp(self):
        """Регистрация пользователя"""
        c.Comment=False 
        return render("/register.mako.html")
    

    def search(self):
        """Поиск в Yottos"""
        query = request.params.get('QueryText') 
        if query:
            return redirect(u"http://yottos.ru/Result.aspx?q=%s" % query)
        else:
            return redirect("http://yottos.ru")
        
        
    def registerToken(self):
        """ Регистрация токена Google """
        c.Comment=False 
        token = request.params.get('token')
        if not token:
            return redirect('/')
        app_globals.db['google.tokens'].insert({'token': token,
                                                'datetime': datetime.now(),
                                                'ip': request.environ['REMOTE_ADDR']  
                                                })
        return render("/token-registered.mako.html")


    def resumeAccount(self, id):
        ''' Возобновление временно заблокированного аккаунта GetMyAd '''
        user = app_globals.db.users.find_one({'login' : id})
        if user.get('blocked') == 'light':
            user['blocked'] = False
            app_globals.db.users.save(user)
        return redirect(url(controller="main", action="index"))
    