# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from formencode import validators as v
from getmyad import model
from getmyad.controllers.advertise import AdvertiseController
from getmyad.controllers.main import MainController
from getmyad.lib import helpers as h
from getmyad.lib.base import BaseController, render
from getmyad.model import AccountReports, Account
from getmyad.tasks.sendmail import sendmail
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals, config
from pylons.controllers.util import abort, redirect
from uuid import uuid1
import formencode
import json
import logging
import os
import pymongo.json_util
import time


log = logging.getLogger(__name__)


def current_user_check(f):
    ''' Декоратор. Проверка есть ли в сессии авторизованный пользователь'''
    def wrapper(*args):
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        c.user = user
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
 

        token = str(uuid1()).upper()
        session[token] = {'user': session.get('user')}
        session.save()
        c.token = token      

        account = model.Account(user)
        try:
            account.load()
        except Account.NotFoundError:
            return MainController().signOut()
            
        ad = AdvertiseController()
        c.updateTime = model.updateTime()
        c.updateTimeKiev = model.updateTime()
        c.updateTimeMoskow = c.updateTimeKiev + timedelta(hours=1)
        c.updateTimeUTC = int(time.mktime(c.updateTime.timetuple()) * 1000)
        c.chartData = ad.days()
        c.summaryReportData = ad.allAdvertises()
        c.accountSumm = account.report.balance()
        c.informers = account.informers()
        c.min_out_sum = account.min_out_sum
        c.moneyOutEnabled = (c.accountSumm >= c.min_out_sum)
        c.money_out_paymentType = account.money_out_paymentType if account.money_out_paymentType else ['webmoney_z']
            
        c.moneyOutEnabled = (c.accountSumm >= c.min_out_sum or account.prepayment)
        c.moneyOutHistory = self.moneyOutHistory()
        domains = account.domains.list()
        requests = account.domains.list_request()
        for x in requests:
            domains.append(str(x) + u' (ожидает подтверждения)')
        if (ad._domainsAdvertises('')):
            domains.append('')    
        c.domains = h.jgridDataWrapper([ ( x , '') for x in domains])
        return render('/statistics.mako.html')
    
 
    @current_user_check
    def accountIncome(self):
        """Возвращает данные о начислении денег на счёт"""
        ads = [x.guid for x in model.Account(c.user).informers()]
        db = app_globals.db
        data = db.stats_daily_adv.group(['date'],
                                        {'adv': {'$in': ads}},
                                        {'sum': 0, 'unique': 0},
                                        'function(o,p) {p.sum += o.totalCost || 0; p.unique += o.clicksUnique || 0; }')
        data.sort(key=lambda x:x['date'])
        data.reverse()
        
        from math import ceil
        try:
            page = int(request.params.get('page'))
            rows = int(request.params.get('rows'))
        except:
            page = 1
            rows = 20
        
        totalPages = int(ceil(float(len(data)) / rows))
        data = data[(page-1)*rows : page*rows]
        data = [{'id': index,
                 'cell': (
                          x['date'].strftime("%d.%m.%Y"),
                          x['unique'],
                          '%.2f $' % (x['sum'] / x['unique']) if x['unique'] else 0,
                          '%.2f $' % x['sum']
                        )
                     }
                    for index, x in enumerate(data)]
        return json.dumps({'total': totalPages,
                           'page': page,
                           'records': len(data),
                           'rows': data
                           },
                           default=pymongo.json_util.default, ensure_ascii=False) 
    
    @current_user_check
    def moneyOutHistory(self):
        """История вывода денег"""
        data = AccountReports(Account(c.user)).money_out_requests()
        data.sort(key=lambda x:x['date'], reverse=True)
        table = []
        for x in data:
            date = x['date'].strftime("%d.%m.%Y")
            summ = h.formatMoney(x['summ'])
            if not x.get('approved'):
                comment = u'заявка обрабатывается...'
            else:
                if x.get('comment'):
                    comment = u"подтверждена: %s" % x.get('comment')
                else:
                    comment = u"подтверждена"
            row = (date, x['paymentType'], summ, comment)
            table.append(row)
        
        return h.jgridDataWrapper(table)
        
        
    @current_user_check 
    @expandtoken    
    @authcheck   
    def moneyOutSubmit(self):
        '''Обработывает поданную заявку на вывод средств'''
        paymentType = request.params.get('moneyOut_paymentType')
        
        if paymentType == 'webmoney_z' :
            return self._moneyOutSubmit_webmoney()
            
        elif paymentType == 'card':
            return self._moneyOutSubmit_card()
        
        elif paymentType == "factura":
            return self._moneyOutSubmit_factura()
            
        else: 
            errorMessage = u'<br/>\n Не выбран тип оплаты'
            return h.JSON({'error': True, 'msg': errorMessage, 'ok': False})

    
    def _moneyOutSubmit_webmoney(self):
        ''' Обработка заявки на вывод средств посредством webmoney '''
        confirm_guid = uuid1().hex
        account = model.Account(c.user)
        account.load()
        balance = AccountReports(account).balance()
        schema = MoneyOutForm_web()
        try:
            form = schema.to_python(dict(request.params))
        except formencode.Invalid, error:
            errorMessage = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
            return h.JSON({'error':True, 'msg': errorMessage, 'ok': False})

        if not account.prepayment:
            if form.get('moneyOut_summ', 0) > balance:
                return h.JSON({'error': True,
                               'msg': u'К выводу доступно не более %s$!' % balance,
                               'ok': False})
        # Сохраняем заявку
        try:    
            app_globals.db.money_out_request.insert(
                    {
                         'date': datetime.now(),
                         'user': {'guid': '',
                                  'login': c.user},
                         'summ': form.get('moneyOut_summ'),
                         'paymentType': 'webmoney_z',
                         'webmoneyLogin': form.get('moneyOut_webmoneyLogin'),
                         'webmoneyAccount': form.get('moneyOut_webmoneyAccountNumber'),
                         'phone': form.get('moneyOut_phone'),
                         'comment': form.get('moneyOut_comment'),
                         'confirm_guid': confirm_guid
                    })
        except:
            return h.JSON({'error': True,
                           'msg': u'Ошибка! Заявка на вывод средств не принята.',
                           'ok': False})
            
        # Отправляем письмо с просьбой подтвердить заявку
        moneyOut_params = u'''    
               Тип вывода средств: webmoney-z
               WMID:               %s
               Номер кошелька:     %s 
               Сумма:              %s $
            ''' % (form['moneyOut_webmoneyLogin'],
                   form['moneyOut_webmoneyAccountNumber'],
                   form['moneyOut_summ'])
        try:
            self._sendRequestToApproveMoneyOut(account.email, moneyOut_params, confirm_guid)
        except Exception as ex:
            log.error('Error while sending confirmation email: %s' % str(ex))

        return h.JSON({'error': False,
                       'ok': True,
                       'msg': u'Заявка успешно принята'})


    def _moneyOutSubmit_card(self):
        ''' Обработка заявки на вывод средств посредством пластиковой карты '''
        confirm_guid = uuid1().hex
        account = model.Account(c.user)
        account.load()
        balance = AccountReports(account).balance()
        schema = MoneyOutForm_card()
        try:
            form = schema.to_python(dict(request.params))
        except formencode.Invalid, error:
            errorMessage = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
            return h.JSON({'error': True, 'msg': errorMessage, 'ok': False})
        
        if not account.prepayment:
            if form.get('moneyOut_cardSumm') > balance:
                return h.JSON({'error': True,
                               'msg': u'К выводу доступно не более %s$!' % balance,
                               'ok': False})
        # Сохраняем заявку
        moneyout_request_object = {
                         'date': datetime.now(),
                         'user': {'guid': '',
                                  'login': c.user},
                         'summ': form.get('moneyOut_cardSumm'),
                         'paymentType': 'card',
                         'cardNumber': form.get('moneyOut_cardNumber'),
                         'cardName': form.get('moneyOut_cardName'),
                         'cardType': form.get('moneyOut_cardType', ''),
                         'phone': form.get('moneyOut_cardPhone'),
                         'expire_year': form.get('moneyOut_cardYear'),
                         'expire_month': form.get('moneyOut_cardMonth'),   
                         'comment': form.get('moneyOut_cardComment'),
                         'bank': form.get('moneyOut_cardBank'),
                         'bank_MFO': form.get('moneyOut_cardBankMFO', ''),
                         'bank_OKPO': form.get('moneyOut_cardBankOKPO', ''),
                         'bank_TransitAccount': form.get('moneyOut_cardBankTransitAccount', ''),
                         'cardCurrency': form.get('moneyOut_cardCurrency'),
                         'confirm_guid': confirm_guid
                    }
        app_globals.db.money_out_request.insert(moneyout_request_object, safe=True)
        
        # Отправляем письмо с подтверждением
        moneyOut_params = u'''
           Тип вывода средств: банковская карта %(cardType)s
           Владелец: %(cardName)s
           Банк: %(bank)s
           МФО банка: %(bank_MFO)s
           ОКПО банка: %(bank_OKPO)s
           Транзитный счёт банка: %(bank_TransitAccount)s
           Номер карты: %(cardNumber)s
           Срок действия карты: %(expire_month)s / %(expire_year)s
           Сумма: %(summ)s $
        ''' % moneyout_request_object
        try:
            self._sendRequestToApproveMoneyOut(account.email, moneyOut_params, confirm_guid)
        except Exception as ex:
            log.error('Error while sending confirmation email: %s' % str(ex))

        return h.JSON({'error': False,
                       'ok': True,
                       'msg': u'Заявка успешно принята'})


    def _moneyOutSubmit_factura(self):
        ''' Обработка заявки на вывод средств посредством счёт-фактуры '''
        confirm_guid = uuid1().hex
        account = model.Account(c.user)
        account.load()
        balance = AccountReports(account).balance()
        schema = MoneyOutForm_factura()
        if not session.get('factura_file_name'):
            return h.JSON({'error': True,
                           'msg': u'Не загружен файл счёт-фактуры!',
                           'ok': False})
        try:
            form = schema.to_python(dict(request.params))
        except formencode.Invalid as error:
            errorMessage = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
            return h.JSON({'error': True, 'msg': errorMessage, 'ok': False})
        
        if not account.prepayment:
            if form.get('moneyOut_facturaSumm') > balance:
                return h.JSON({'error':True,
                               'msg': u'К выводу доступно не более %s$!' % balance,
                               'ok': False})
                
        # Сохраняем заявку
        app_globals.db.money_out_request.insert(
                    {
                         'date': datetime.now(),
                         'user': {'guid': '',
                                  'login': c.user},
                         'summ': form.get('moneyOut_facturaSumm'),
                         'paymentType': 'factura',
                         'contact': form.get('moneyOut_facturaContact'),
                         'phone': form.get('moneyOut_facturaPhone'),
                         'comment': form.get('moneyOut_facturaComment'),
                         'confirm_guid': confirm_guid,
                         'schet_factura_file_name': session.get('factura_file_name')
                    })
        
        # Отправляем письмо с подтверждением вывода
        moneyOut_params = u'''
               Вывод средств посредством счёт-фактуры.
               Сумма к выводу: %s $
            ''' % form['moneyOut_facturaSumm']
        try:
            self._sendRequestToApproveMoneyOut(account.email, moneyOut_params, confirm_guid)
        except Exception as ex:
            log.error('Error while sending confirmation email: %s' % str(ex))

        return h.JSON({'error': False,
                       'ok': True,
                       'msg': u'Заявка успешно принята'})
    
    
    @current_user_check
    @expandtoken    
    @authcheck
    def moneyOutRemove(self):
        ''' Отмена заявки на вывод средств'''
        try:
            id = int(request.params.get('id'))
            obj = app_globals.db.money_out_request.find({'user.login': c.user}).sort('date', pymongo.DESCENDING)[id-1]
            if obj.get('approved', False):
                return h.JSON({'error': True, 'msg': u'Эта заявка уже была выполнена'})
            app_globals.db.money_out_request.remove(obj, safe=True)
        except:
            return h.JSON({'error': True, 'ok': False})
        return h.JSON({'error': False, 'ok': True, 'msg': u'Заявка успешно отменена'})
       
    @current_user_check
    @expandtoken    
    @authcheck
    def register_domain_request(self):
        ''' Добавление заявки на регистрацию домена'''
        try:
            schema = RegisterDomainRequestForm()
            form = schema.to_python(dict(request.params))
            domain = form['txtRegisterDomainUrl']
            account = Account(login=c.user)
            account.domains.add_request(domain)
        except formencode.Invalid, error:
            errorMessage = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
            return h.JSON({'error': True, 'msg': errorMessage})
        except Account.Domains.AlreadyExistsError:
            return h.JSON({'error': True, 'msg': u"Данный домен уже был зарегистрирован"})
        except:
            raise
            return h.JSON({'error': True})
        else:
            return h.JSON({'error': False})
    
    
    def confirmRequestToApproveMoneyOut(self, id):
        ''' Подтверждение заявки на вывод средств по выданной ссылке '''
        try:
            c.text_message = u''
            money_out_request = app_globals.db.money_out_request.find_one({'confirm_guid': id})
             
            if not money_out_request:
                raise UserWarning(u'''
                    <h2>Заявки не существует</h2>
                    <p>Возможно, Вы уже отозвали данную заявку на вывод средств</p>''')
                
            if money_out_request['date'] - datetime.today() > timedelta(days=3):
                raise UserWarning(u'''
                    <h2>Извините! Ваша заявка устарела.</h2>
                    <p>Пожалуйста, оформите новую заявку в личном кабинете.</p>''')
                
            if money_out_request.get('user_confirmed'):
                raise UserWarning(u'''
                    <h2>Заявка уже была подтверждена!</h2>''')
            
            money_out_request['user_confirmed'] = True
            app_globals.db.money_out_request.save(money_out_request, safe=True)
            
        except UserWarning as ex:
            c.text_message = unicode(ex)
            
        except Exception as ex:
            c.text_message = u'''
                <h2>Произошла ошибка! </h2>
                <p> Заявка не была подтверждена. Пожалуйста, свяжитесь с
                    вашим менеджером!</p>
                <p>Техническая информация: %s.</p>''' % str(ex)
        else:
            c.text_message = u'''
                <h2> Заявка подтверждена.</h2>
                <p>Спасибо за участие в программе GetMyAd!</p>'''

        footer = u"""
            <br/><p style="font-style:italic;">С уважением,<br/>
            Отдел Развития Рекламной Сети Yottos GetMyAd.<br/>
            partner@yottos.com<br/>
            тел.: +38 (050) 406 20 20.</p>"""
        c.text_message = c.text_message + footer
        return render('/thanks_user.mako.html')
    
       
    def _sendRequestToApproveMoneyOut(self, email, money_out_params, confirm_guid):
        ''' Отправка письма с требованием подтвердить вывод средств
            на e-mail пользователя '''

        confirm_link = "http://getmyad.yottos.com/private/confirmRequestToApproveMoneyOut/%s" % confirm_guid
                
        if request.environ['SERVER_NAME'].endswith('.com.ua'):
            domain = 'com.ua'
        elif request.environ['SERVER_NAME'].endswith('ru'):
            domain = 'ru'
        elif request.environ['SERVER_NAME'].endswith('com'):
            domain = 'com'
        else:
            domain = 'com'
        
        date_expire = (datetime.today() + timedelta(days=3)).strftime('%d.%m.%y %H:%M')

        subject = u'Подтверждение заявки на вывод средств в Yottos GetMyAd'
        mail_text = u'''
            Здравствуйте!
            
            Вы получили это письмо, так как Ваш e-mail был использован при регистрации на сайте http://getmyad.yottos.%s
            Если Вы не регистрировались на указанном сайте, просто проигнорируйте и удалите это письмо.
            
            Параметры вывода средств:
            %s
            
            Для продолжения заявки на вывод средств в Yottos GetMyAd
            проследуйте по следующей ссылке: 
            %s

            Высланная Вам ссылка для подтверждения будет актуальна в течение 3-х ближайших суток (до %s)
            
            Это автоматическое письмо. Если у вас есть какие-либо вопросы, Вы можете
            изучить Справочную информацию: http://getmyad.yottos.%s/info/answers
            или обратиться к Вашему менеджеру.
            
            
            С уважением,
            Коллектив Yottos GetMyAd
            http://getmyad.yottos.com''' \
            % (domain, money_out_params, confirm_link, date_expire, domain)

        sendmail(email, subject, mail_text)
        
    
    @current_user_check
    def removeUploadFactura(self):
        try:
            filename = session.get('factura_file_name')
            os.remove('%s/%s' % (config.get('schet_factura_folder'), filename))
            session['factura_file_name'] = ''
            session.save()
        except:
            return h.JSON({'error': True, 'msg': u'Ошибка удаления файла!'})
        return h.JSON({'error': False})
        

    @current_user_check    
    def uploadFactura(self):
        try:
            form = request.params.get("userfile")
            file_guid = str(uuid1().hex).upper()
            x = form.filename
            extension = os.path.splitext(form.filename)[-1]
            filename = file_guid + extension
            location = '%s/%s' % (config.get('schet_factura_folder'), filename)
            dir = os.path.dirname(location)
            if not os.path.exists(dir):
                os.mkdir(dir)
            file_on_server = open(location, 'w')
            file_on_server.write(form.value)
            file_on_server.close()
            session['factura_file_name'] = filename
            session.save()
        except:
            return h.JSON({'error': True})
        return h.JSON({'error': False})    
        
        
        
class MoneyOutForm_web(formencode.Schema):
    """Форма вывода денег на web money"""
    allow_extra_fields = True
    filter_extra_fields = True
    moneyOut_summ = v.Number(min=10,
                             not_empty=True,
                             messages={'empty': u'Пожалуйста, введите сумму!',
                                       'number': u'Пожалуйста, введите корректную сумму!',
                                       'tooLow': u'Сумма должна быть не менее %(min)s $!'})
    moneyOut_webmoneyLogin = v.Regex(regex='^[0-9]{12}$', 
                                     not_empty=True,
                                     messages={'empty': u'Пожалуйста, введите WMID!',
                                               'invalid': u'WMID должен состоять из 12 цифр!'})
    moneyOut_webmoneyAccountNumber = v.Regex(regex='^[Zz][0-9]{12}$',
                                             not_empty=True,
                                             messages={'empty': u'Пожалуйста, введите номер кошелька WebMoney!',
                                                       'invalid': u'Номер кошелька состоит из Z и 12 цифр!'})
    moneyOut_phone = v.NotEmpty(messages={'empty': u'Пожалуйста, введите номер телефона!'})
    moneyOut_comment = v.String(if_missing=None)
    
class MoneyOutForm_card(formencode.Schema):
    """Форма вывода денег на пластиковую карту"""
    allow_extra_fields = True
    filter_extra_fields = True
    moneyOut_cardSumm = v.Number(min=10,
                             not_empty=True,
                             messages={'empty': u'Пожалуйста, введите сумму!',
                                       'number': u'Пожалуйста, введите корректную сумму!',
                                       'tooLow': u'Сумма должна быть не менее %(min)s $!'})
    moneyOut_cardName = v.NotEmpty(messages={'empty': u'Пожалуйста, введите имя владельца карты!'})
    moneyOut_cardNumber = v.Regex(regex='^(\d{4}[ -]?){3}\d{4}$',
                             not_empty=True,
                             messages={'empty': u'Пожалуйста, укажите номер пластиковой карты!',
                                       'invalid': u'Номер карты должен состоять из 16 цифр!'})
    moneyOut_cardMonth = v.NotEmpty(messages={'empty': u'Пожалуйста, укажите месяц до которго возможно использование пластиковой карты!'})
    moneyOut_cardYear = v.NotEmpty(messages={'empty': u'Пожалуйста, укажите год до которго возможно использование пластиковой карты!'})
    moneyOut_cardBank = v.NotEmpty(messages={'empty': u'Пожалуйста, укажите название банка!'})
    moneyOut_cardType = v.String(if_missing=None)
    moneyOut_cardPhone = v.NotEmpty(messages={'empty': u'Пожалуйста, укажите контактный телефон!'})
    moneyOut_cardComment = v.String(if_missing=None)
    moneyOut_cardCurrency = v.String(if_missing=None)
    moneyOut_cardBankMFO = v.Regex(regex="^\d{6}$",
                                   messages={'invalid': u'МФО банка должен состоять из 6 цифр!'}) 
    moneyOut_cardBankOKPO = v.Regex(regex="^\d{10}$",
                                   messages={'invalid': u'ОКПО банка должен состоять из 10 цифр!'}) 
    moneyOut_cardBankTransitAccount = v.Regex(regex="^\d{13}$",
                                   messages={'invalid': u'Транзитый счёт должен состоять из 13 цифр!'}) 
    
class MoneyOutForm_factura(formencode.Schema):
    """Форма вывода денег на пластиковую карту"""
    allow_extra_fields = True
    filter_extra_fields = True
    moneyOut_facturaSumm = v.Number(min=10,
                                    not_empty=True,
                                    messages={'empty': u'Укажите сумму вывода!',
                                              'number': u'Укажите корректную сумму!',
                                              'tooLow': u'Сумма должна быть не менее %(min)s $!'})
    moneyOut_facturaContact = v.NotEmpty(messages={'empty': u'Пожалуйста, укажите контактное лицо!'})
    moneyOut_facturaPhone = v.NotEmpty(messages={'empty': u'Пожалуйста, укажите номер телефона!'})
    moneyOut_facturaComment = v.String(if_missing=None)
    
  
    

class RegisterDomainRequestForm(formencode.Schema):
    ''' Форма заявки на регистрацию домена '''
    allow_extra_fields = True
    filter_extra_fields = True
    txtRegisterDomainUrl = v.URL(add_http = True,
                                 check_exists = True,
                                 not_empty=True,
                                 messages={'badURL': u'Неверный формат ссылки!',
                                           'notFound': u'Указанный адрес не найден!',
                                           'noTLD': u'Вы должны указать полное доменное имя (например, %(domain)s.com)',
                                           'httpError': u'Во время попытки обращения к данному адресу возникла ошибка: %(error)s',
                                           'socketError': u'Во время попытки обращения к серверу возникла ошибка: %(error)s',
                                           'empty': u'Пожалуйста, введите url сайта!'
                                           })
    
    
