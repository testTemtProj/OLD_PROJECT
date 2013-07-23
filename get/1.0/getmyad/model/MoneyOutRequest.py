# This Python file uses the following encoding: utf-8
from getmyad.model.Account import AccountReports, Account
from getmyad.tasks.sendmail import sendmail
from pylons import app_globals
import datetime
import uuid



class MoneyOutRequest(object):
    '''Запрос на вывод средств'''
    
    class NotEnoughMoney(Exception):
        ''' Недостаточно денег для формирования заявки '''
        pass
    
    def __init__(self):
        self.date = datetime.datetime.now()
        self.account = None
        self.summ = 0
        self.comment = ''
        self.confirm_guid = uuid.uuid1().hex
        self.ip = ''
    
    def save(self):
        ''' Сохранение заявки '''
        if not self._check_money_out_possibility():
            raise MoneyOutRequest.NotEnoughMoney()
            
        req = {'date': self.date,
               'summ': self.summ,
               'confirm_guid': self.confirm_guid,
               'user': {'login': self.account.login},
               'comment': self.comment,
               'ip': self.ip
               }
        print req
        payment_details = self._get_payment_details()
        assert isinstance(payment_details, dict)
        req.update(payment_details)
        app_globals.db.money_out_request.save(req, safe=True)
        print "Saving: %s" % req
    
    def _get_payment_details(self):
        ''' Возвращает словарь со свойствами, специфичными для каждого метода оплаты '''
        return {}
    
    def _get_payment_details_for_email(self):
        ''' Текстовое описание подробностей метода вывода для отправки по e-mail '''
        return ''

    def _check_money_out_possibility(self):
        ''' Возвращает true, если заявку с заданными параметрами возможно 
            создать (у клиента должно быть достаточно денег на счету и т.д.) '''
        if not self.account.loaded:
            self.account.load()
        if not self.account.prepayment:
            balance = AccountReports(self.account).balance()
            if self.summ > balance:
                return False
        return True
    
    def _validate_fields(self):
        ''' Проверка полей на корректность '''
        # TODO: Not implemented! 
        pass

    def send_confirmation_email(self):
        ''' Отправка письма на e-mail пользователя с требованием подтвердить вывод средств '''
        if not self.account.loaded:
            self.account.load()
        email = self.account.email
        payment_details = self._get_payment_details_for_email()
        confirm_link = "http://getmyad.yottos.com/private/confirmRequestToApproveMoneyOut/%s" % self.confirm_guid
        date_expire = (datetime.datetime.today() + datetime.timedelta(days=3)).strftime('%d.%m.%y %H:%M')
        subject = u'Подтверждение заявки на вывод средств в Yottos GetMyAd'
        mail_text = u'''
Здравствуйте!

Вы получили это письмо, так как Ваш e-mail был использован при регистрации на сайте http://getmyad.yottos.%s
Если Вы не регистрировались на указанном сайте, просто проигнорируйте и удалите это письмо.

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
            % ('com', payment_details, confirm_link, date_expire, 'com')

        sendmail(email, subject, mail_text)


    def load(self, confirm_guid):
        ''' Загружает заявку с кодом подтверждения confirm_guid '''
        x = app_globals.db.money_out_request.find_one({'confirm_guid': confirm_guid})
        self.date = x['date']
        self.account = Account(x['user']['login'])
        self.comment = x['comment']
        self.confirm_guid = x['confirm_guid']
        self.summ = x['summ'] 


class WebmoneyMoneyOutRequest(MoneyOutRequest):
    ''' Запрос на вывод средств посредством WebMoney '''
    
    def __init__(self):
        MoneyOutRequest.__init__(self)
        self.webmoney_login = ''
        self.webmoney_account_number = ''
        self.phone = ''
    
    def _get_payment_details(self):
        return {'paymentType': 'webmoney_z',
                'webmoneyLogin': self.webmoney_login,
                'webmoneyAccount': self.webmoney_account_number,
                'phone': self.phone
                }

    def _get_payment_details_for_email(self):
        return u'''
Сумма: %s $
Тип вывода средств: webmoney-z'
WMID: %s
Номер кошелька: %s 
 ''' % (self.summ, 
        self.webmoney_login,
        self.webmoney_account_number)



class CardMoneyOutRequest(MoneyOutRequest):
    ''' Запрос на вывод средств посредством банковской карты '''
    
    def __init__(self):
        MoneyOutRequest.__init__(self)
        self.card_number = ''
        self.card_name = ''
        self.card_type = ''
        self.card_phone = ''
        self.expire_year = ''
        self.expire_month = ''
        self.bank = ''
        self.bank_mfo = ''
        self.bank_okpo = ''
        self.bank_transit_account = ''
        self.card_currency = ''
        
    def _get_payment_details(self):
        return { 'paymentType': 'card',
                 'cardNumber': self.card_number,
                 'cardName': self.card_name,
                 'cardType': self.card_type,
                 'phone': self.card_phone,
                 'expire_year': self.expire_year,
                 'expire_month': self.expire_month,
                 'bank': self.bank,
                 'bank_MFO': self.bank_mfo,
                 'bank_OKPO': self.bank_okpo,
                 'bank_TransitAccount': self.bank_transit_account,
                 'cardCurrency': self.card_currency
               }
    
    def _get_payment_details_for_email(self):
        return u'''
Тип вывода средств: банковская карта %(cardType)s
Владелец: %(cardName)s
Банк: %(bank)s
МФО банка: %(bank_MFO)s
ОКПО банка: %(bank_OKPO)s
Транзитный счёт банка: %(bank_TransitAccount)s
Номер карты: %(cardNumber)s
Срок действия карты: %(expire_month)s / %(expire_year)s
''' % self._get_payment_details() + \
u'''Сумма: %s $
''' % self.summ



class InvoiceMoneyOutRequest(MoneyOutRequest):
    ''' Запрос на вывод средств посредством счёт-фактуры '''
    
    def __init__(self):
        MoneyOutRequest.__init__(self)
        self.contacts = ''
        self.phone = ''
        self.invoice_filename = ''
    
    def _get_payment_details(self):
        return { 'paymentType': 'factura',
                 'contact': self.contacts,
                 'phone': self.phone,
                 'schet_factura_file_name': self.invoice_filename
               }
    
    def _get_payment_details_for_email(self):
        return u'''
Вывод средств посредством счёт-фактуры.
'''


class YandexMoneyOutRequest(MoneyOutRequest):
    ''' Запрос на вывод средств посредством Яндекс.Деньги '''
    def __init__(self):
        MoneyOutRequest.__init__(self)
        self.yandex_number = ''
        self.phone = ''
        
    def _get_payment_details(self):
        return {'paymentType': 'yandex',
                'yandex_number': self.yandex_number,
                'phone': self.phone
                }

    def _get_payment_details_for_email(self):
        return u'''Сумма: %s $
                   Тип вывода средств: Яндекс.Деньги'
                   Номер счета: %s''' % (self.summ,  self.yandex_number)
