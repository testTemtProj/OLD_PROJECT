# -*- coding: utf-8 -*-
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from getmyad.lib.base import BaseController, render

log = logging.getLogger(__name__)

class InfoController(BaseController):

    def index(self):
        return self.terms_and_conditions()
    
    def faq(self):
        """Часто задаваемые вопросы"""
        return render('/faq.mako.html')

    def terms_and_conditions(self):
        """Общие условия программы GetMyAd"""
        return render('/terms-and-conditions.mako.html')
    
    def rules(self):
        """Правила программы GetMyAd"""
        return render('/rules.mako.html')
    
    def growing(self):
        """Рост доходности"""
        return render("/growing.mako.html")
    
    def env(self):
        """Переменные окружения"""
        t = url(controller='info', action='rules', qualified=True) + '\n\n\n'
        
        return t + "\n".join(['%s=%s' % x for x in request.environ.items()])