# -*- coding: utf-8 -*-
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import json
import getmyad.lib.helpers as h
from getmyad.lib.base import BaseController, render

log = logging.getLogger(__name__)

class TestAjaxController(BaseController):
    def index(self):        
        
        return render('/test_ajax.mako.html')  


    def getdata(self):
        res=[]
        res.append({'ads':'1Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'2Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'3Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'4Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'5Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'6Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'7Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'8Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        res.append({'ads':'9Теперь доступно и вашему вниманию!','desc':'Выравнивает, подкручивает волосы, делает их блестящими и объемными!','cost':'1 234,00 грн', 'img':'"http://rynok.yottos.ru/img/55/5232348e-b849-46e4-a1d3-ac26135c05dc.jpg"'})
        
        x = request.params.get('exclude', "")
        print x
        #f = open('d:/workfile.txt', 'w+')
        #f.write(str(x))
        #return h.JSON(res)        
        try:
            import urllib 
            URL = 'http://rg.yottos.com/adshow.fcgi?scr=EDE791D1-901A-11DF-8EEC-0015175ECAD8&show=json'
            f = urllib.urlopen(URL)                
            return f.read()
        except IOError, ex:
            return str(ex)                
        finally:
            f.close()
        
        
