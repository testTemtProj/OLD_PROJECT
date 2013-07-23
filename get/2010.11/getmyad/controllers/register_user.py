# -*- coding: utf-8 -*-
import logging
import datetime
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import os
import StringIO
from getmyad.tasks.sendmail import sendmail
from getmyad.lib.base import BaseController, render
from getmyad.lib.capcha import Capcha

log = logging.getLogger(__name__)


class RegisterUserController(BaseController):
    ''' Регистрация пользователя '''
    
    def index(self):
        c.user_name = session.pop('user_name', '')
        c.user_url = session.pop('user_url', '')
        c.user_phone = session.pop('user_phone', '')
        c.user_email = session.pop('user_email', '')
        c.capcha_error = session.pop('capcha_error', '')
        session.save()
        return render('/register_user.mako.html')
    
    def capcha(self):
        ''' Возвращает изображение капчи '''
        c = Capcha()
        c.font_file = os.path.join(os.path.dirname(__file__), '../public/font/myfont.ttf')
        c.generate()
        
        session["register_capcha"] = c.text
        session.save()
        buffer = StringIO.StringIO()
        c.image.save(buffer, "PNG")
        
        return buffer.getvalue()

    def send(self):
        res = request.params      
        if res.get('Capcha') <> session.get("register_capcha"):
            session['user_name'] = res.get('UserNameText')
            session['user_url'] = res.get('SiteUrl')
            session['user_email'] = res.get('Email')
            session['user_phone'] = res.get('PhoneNumber')
            session['capcha_error'] = u'Неверно введены цифры с картинки. Попробуйте ещё раз.'
            session.save()
            return redirect(url(controller="register_user", action="index"))
            
        
        #=======================================================================
        # Отправляем письмо на нашу почту
        #=======================================================================
        our_email = ['partner@yottos.com']    # получатель
        subj = u'Заявка на регистрацию в GetMyAd'
        text = u"""
        Name: %s
        Url: %s
        E-mail: %s
        Телефон: %s
        Время: %s""" % (res['UserNameText'], res['SiteUrl'], res['Email'],
                        res['PhoneNumber'],datetime.datetime.now())

        sendmail(our_email, subj, text)                    

        #=======================================================================
        # Отправляем письмо пользователю
        #=======================================================================
        email = res.get('Email')
        subj = u'Рекламная сеть Yottos - заявка на участие сайта %s' % res['SiteUrl']
        text = u"""
        Здравствуйте, %s!
        Спасибо за интерес к участию в партнёрской программе Yottos GetMyAd.

        Мы обязательно рассмотрим Вашу заявку в течение трех дней и дадим ответ о 
        возможности участия сайта %s в рекламной сети Yottos GetMyAd. 
        (http://getmyad.yottos.com/info/terms_and_conditions). 

        С уважением, 
        Отдел Развития Рекламной Сети Yottos GetMyAd. 
        partner@yottos.com 
        тел.: +38 (050) 406 20 20.


        P.S. Не отвечайте на это письмо! E-mail для связи: partner@yottos.com.
        """ % (res['UserNameText'], res['SiteUrl'])

        sendmail(email, subj, text)
        
        return redirect('/register_user/thanks')

         
    def thanks(self):
        c.text_message = """
<h3>Спасибо за интерес к участию в партнёрской программе Yottos GetMyAd.</h3>
        <p>
        Мы обязательно рассмотрим Вашу заявку в течение трех дней и дадим ответ о <br />
        возможности участия вашего сайта в рекламной сети Yottos GetMyAd. <br />
        (<a href='http://getmyad.yottos.com/info/terms_and_conditions'>http://getmyad.yottos.com/info/terms_and_conditions</a>). <br />
</p>
<br />
        <p>С уважением,</p> 
        <p>Отдел Развития Рекламной Сети Yottos GetMyAd.</p> 
        <p>partner@yottos.com</p> 
        <p>тел.: +38 (050) 406 20 20.</p>        
        """
        return render('/thanks_user.mako.html')
