# coding: utf-8
from datetime import timedelta
import logging
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.decorators import jsonify
from pylons.controllers.util import abort, redirect

from parseryml.lib.base import BaseController, render
from parseryml.model.baseModel import Base
from parseryml.model.marketModel import MarketModel
from parseryml.lib import helpers as h


from parseryml.model.userModel import UserModel
from parseryml.lib.tasks import parse_by_id

import smtplib
from email.MIMEText import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import logging
log = logging.getLogger(__name__)

class ParserSettingsController(BaseController):
    def __init__(self):
        self.categories = None        

    def index(self):
        if session.has_key('login'):
            if session['login']:
                return render('/parser_settings/parser.mako.html')
            else:
                return render('/login/login.mako.html')
        else:
            return render('/login/login.mako.html')

    def login(self):
        UM = UserModel()
        if UM.check_user_pwd(request.params.get('user_login'), request.params.get('user_password')):
            session['login'] = True
            session.save()
        else:
            session['login'] = False
            session.save()
            return u'Не верный Логин или пароль'

    def exit(self):
        if session.has_key('login'):
            session['login'] = False
            session.save()
        return

    def set_time_settings(self):
        MM = MarketModel()
        params = request.params.get('params', "{}")
        params = h.FJSON(params)
        if not params['interval']:
            params = None
        MM.set_time_settings(request.params.get('market_id'), params)
        return

    @jsonify
    def get_states(self):
        stack = request.params.getall('markets[]')
        market_ids = [0]
        for market_id in stack:
            market_ids.append(int(market_id))
        market = MarketModel()
        return {'states':market.get_states(market_ids)}

    @jsonify
    def get_markets(self):
        MM = MarketModel()
        limit = request.params.get('limit', 20)
        start = request.params.get('start', 0)
        sort_by = request.params.get('sort')
        sort_dir = request.params.get('dir')
        pattern = request.params.get('pattern', '')
        group = request.params.get('groupBy', '')
        if sort_dir == 'ASC':
            sort_dir = 1
        else:
            sort_dir = -1
            
        markets = MM.get_all(start, limit, sort_by, sort_dir, pattern, group)

        products = []

        total = MM.get_count(pattern)

        for market in markets:
            result = {
                'id':               market.get('id', ""),
                'file_date':        str(market.get('file_date', "")),
                'date_create':      str(market.get('dateCreate', "")),
                'title':            market.get('title', ""),
                'status':           market.get('state', ""),
                'urlExport':        market.get('urlExport', ""),
                'urlMarket':        market.get('urlMarket', ""),
                'last_update':      str(market.get('last_update', "")),
                'time_setting':     market.get('time_setting', ""),
                'interval':         market.get('interval', 0),
                'status_id':        market.get('status_id', 0),
                'categories_count': 0,
                'offers_count':     0,
                'started':          "",
                'finished':         "",
                'delta':            {},
            }

            categories = market.get('Categories', None)
            if categories is not None:
                result['categories_count'] = len(categories)

            offersModel = Base.get_offer_collection()
            result['offers_count'] = offersModel.find({'shopId':result['id']},{'title':1}).count()
                
            if result['interval'] == 0:
                if 'time_setting' in result and 'interval' in result['time_setting'] and 'interval_count' in result['time_setting']:
                    argument = 0
                    if result['time_setting']['interval'] == u'час':
                        argument = 2400
                    elif result['time_setting']['interval'] == u'день':
                        argument = 100
                    elif result['time_setting']['interval'] == u'месяц':
                        argument = 10
                    elif result['time_setting']['interval'] == u'год':
                        argument = 1

                    result['interval'] = argument * result['time_setting']['interval_count']

                    data = {'id':result['id'], 'interval':result['interval']}
                    MM.save(data)
            
            if 'status' in result and 'state' in result['status']:
                if 'started' in result['status']:
                    result['started']  = str(result['status']['started'])
                    if 'finished' in result['status']:
                        result['finished'] = str(result['status']['finished'])

                        delta = result['status']['finished'] - result['status']['started']
                        result['delta'] = {
                            'days': delta.days,
                            'sec': delta.seconds
                        }
                        
                        del result['status']['finished']
                        
                    del result['status']['started']

                if result['status']['state'] == 'finished':
                    argument = 1
                elif result['status']['state'] == 'error':
                    argument = 2
                elif result['status']['state'] == 'aborted':
                    argument = 3
                elif result['status']['state'] == 'parsing':
                    argument = 20
                elif result['status']['state'] == 'pending':
                    argument = 5
                else:
                    argument = 10
            else:
                argument = 10
                result['status'] = {'state':'new'}
                data = {'id':result['id'], 'state':result['status']}
                MM.save(data)

            if result['status_id'] != argument:
                result['status_id'] = argument
                data = {'id':result['id'], 'status_id':result['status_id']}
                MM.save(data)
                
            products.append(result)

        result = {"total": str(total), "data": products}

        session.save()

        return result

    @jsonify
    def start_parsing_market(self):
        market_id = int(request.params.get('market_id'))
        
        data = {
            'id': market_id,
            'state': {
                'state':'parsing',
            }
        }
        
        market = MarketModel()
        market.save(data)

        parse_by_id.apply_async(args=[market_id], queue="parse_yml_task", routing_key="parseryml.process")
        return {'result': 'success'}

    def send_email(self, market_id, email):
        # отправитель
        me = 'rynok_parser@yottos.com'
        # получатель
        you = email
        # текст письма
        text = 'Это письмо к вам пришло потому что в файле выгрузки есть не валидные продукты список их прикреплен в файле'
        text = msg = MIMEText(text, _charset="utf-8")
        # заголовок письма
        subj = 'Hello!!'
        # параметры SMTP-сервера
        server = "yottos.com" # "smtp.mail.ru"
        port = 26
        user_name = "support@yottos.com"
        user_passwd = "57fd8824"

        msg = MIMEMultipart()
        msg['Subject'] = subj
        msg['From'] = me
        msg['To'] = you

        path = 'parseryml/public/not_valid/' + str(market_id) + '.txt'
        attach = MIMEApplication(open(path, 'r').read())
        attach.add_header('Content-Disposition', 'attachment', filename='errors.txt')
        msg.attach(text)
        msg.attach(attach)

        s = smtplib.SMTP(server, port)
        s.starttls()
        s.set_debuglevel(5)
        s.login(user_name, user_passwd)
        s.sendmail(me, you, msg.as_string())
        s.quit()