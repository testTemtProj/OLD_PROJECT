# encoding: utf-8
from getmyad.lib import helpers as h
from getmyad.lib.base import BaseController, render
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators import jsonify
import base64
import datetime
import json
import logging
import pymongo
import time


log = logging.getLogger(__name__)
db = pymongo.Connection('vsrv-2.3.yottos.com').attractor    # TODO: Вынести настройку подключения в конфиг


def current_user_check(f):
    ''' Декоратор. Проверка есть ли в сессии авторизованный пользователь'''
    def wrapper(*args):
        user = request.environ.get('CURRENT_ATTRACTOR_USER')
        if not user: return h.userNotAuthorizedError()
        c.manager_login = user
        return f(*args)
    return wrapper


class AttractorController(BaseController):

    def __before__(self, action, **params):
        user = session.get('attractor_user')
        if user:
            c.user = user
            request.environ['CURRENT_ATTRACTOR_USER'] = user
        else:
            c.user = ''

    def index(self):
        # TODO: Сделать главную страницу
        return ''' <html>
            <body>
              <div>
                <form action="/attractor/checkPassword" method="post" id="login_form" name="login_form">
                  <table>
                    <tr>
                      <td><b/><label for="login">Логин</label></td>
                      <td><input id="login" name="login"/></td>
                    </tr>        
                    <tr>
                      <td><b/><label for="password">Пароль</label></td>
                      <td><input type="password" id="password" name="password"/></td>
                    </tr>  
                    <tr>
                      <td><input type="submit" value="Вход" id="enter" name="enter"/></td>
                    </tr>
                  </table>  
                </form>
              </div>
            </body>
            </html>
            ''' 

    def checkPassword(self):
        ''' Проверка пароля и пользователя'''
        try:
            login = request.params.get('login')
            password = request.params.get('password')
            if not (login == 'yottos') or not (password == '123123'):
                return self.index()
            session['attractor_user'] = login
            session.save()
            request.environ['CURRENT_ATTRACTOR_USER'] = login
        except:
            return self.index()   
        return h.redirect('/attractor/main')


    @jsonify
    def session_check(self):
        ''' Проверка действительности сессии пользователя Attractor.
            
            Возвращает JSON с одним булевым полем ``ok``.
        '''
        session_valid = 'CURRENT_ATTRACTOR_USER' in request.environ
        return {'ok': session_valid}

    def main(self):
        if 'CURRENT_ATTRACTOR_USER' not in request.environ:
            return h.redirect('/attractor/index')
        return render('/attractor/main.mako.html')

    @current_user_check
    def script_users(self):
        ''' Возвращает список пользователей, установивших скрипт Attractor.
            Формат: JSON для таблицы jqGrid '''
        users = []
        for user in db.users.find({'hidden': {'$ne': True}}).sort('id'):
            row = (user['id'],)
            users.append(row)
        return h.jgridDataWrapper(users)
    
    @current_user_check
    def data(self):
        ''' Возвращаем данные для таблицы статистики. 
            Понимает страницы, сортировку и прочие фичи jqGrid.
            
            Ожидает следующие GET-параметры::

            site
                ?

            start_date
                Дата начала отчётного периода в формате dd.mm.yyyy
                По умолчанию 01.01.2001
            
            end_date
                Дата конца отчётного периода в формате dd.mm.yyyy
                По умолчанию 01.01.2020
            
            scope
                Если равен ``partners``, то вернёт только сайты-партнёры getmyad.
                Если равен ``others``, то вернёт только посторонние сайты.
                По умолчанию равен ``partners``.

            relative
                если равен ``true``, то вернёт относительные данные, 
                в процентах. Если не задан, будет возвращать абсолютные
                данные.

            page (?)
                номер текущей странцы (для пейджинга)

            rows
                количество записей на странице
            
            sidx
                название колонки для сортировки

            sord
                порядок сортировки: ``asc`` -- по возрастанию, ``desc`` --
                по убыванию
        '''
        #---------------------------------------------------- Выделяем параметры
        try:
            domain = str(request.params['site']).replace("'", "")
            start_date = request.params.get('start_date') or '01.01.2001'
            end_date = request.params.get('end_date') or '01.01.2020'
            scope = request.params.get('scope', 'partners')
            if scope not in ['partners', 'others']:
                scope = 'partners' 
            relative = request.params.get('relative', '') == 'true'
            try:
                rows = int(request.params.get('rows', 100))
                page = int(request.params.get('page', 1))
            except ValueError:
                rows = 100
                page = 1

        except KeyError as ex:
            return json.dumps({'error': True, 
                               'msg': 'Param %s not specified' % ex})
         
        d1 = datetime.datetime(*time.strptime(start_date, "%d.%m.%Y")[0:5])
        d2 = datetime.datetime(*time.strptime(end_date, "%d.%m.%Y")[0:5])          
        
        #------------------------------------------------------- Получаем данные
        data = self._get_data(domain, d1, d2, scope, relative)

        #--------------------------------------------- Помещаем данные в таблицу
        table = []
        for referrer, x in data.items():

            # Количество людей, записанных аттрактором
            noticed_by_attractor = x['15'] + x['30'] + x['60']

            # Средняя глубина просмотра
            if noticed_by_attractor and x['depth']:
                depth = round(1.0 * x['depth'] / noticed_by_attractor, 2)
            else:
                depth = 0

            # Строка таблицы
            if not relative:
                row = (referrer, x['total'], x['3'], x['15'], x['30'], x['60'], depth)
            else:
                row = (referrer, x['total'], x['3_rel'], x['15_rel'], x['30_rel'],
                       x['60_rel'], depth)

            table.append(row)
            
        #------------------------------------------------------------ Сортировка
        sort_column = request.params.get('sidx')
        sort_order = request.params.get('sord', 'asc')
        columns = ['partner', 'time_all', 'time_percent_3', 'time_percent_15',
                   'time_percent_30', 'time_percent_60', 'depth']
        if sort_column in columns:
            index = columns.index(sort_column)
            table.sort(key=lambda x: x[index], reverse=(sort_order=='desc') )

        #----------------------------------------------------------------- Итоги
        values = data.values()
        sum_all = sum(x['total'] for x in values) or 100 # для защиты от деления на 0
        sum_noticed_by_attractor = \
            sum(x['15'] + x['30'] + x['60'] for x in values)
        sum_3 = sum(x['3'] for x in values)
        sum_15 = sum(x['15'] for x in values)
        sum_30 = sum(x['30'] for x in values)
        sum_60 = sum(x['60'] for x in values)
        sum_depth = sum(x['depth'] for x in values)
        try:
            avg_depth = round(float(sum_depth) / float(sum_noticed_by_attractor), 2)
        except ZeroDivisionError:
            avg_depth = 0
        if relative:
            userdata = {'parther': '',
                        'time_all': sum_all,
                        'time_percent_3': '%d%%' % int(100.0 * sum_3 / sum_all),
                        'time_percent_15': '%d%%' % int(100.0 * sum_15 / sum_all),
                        'time_percent_30': '%d%%' % int(100.0 * sum_30 / sum_all),
                        'time_percent_60': '%d%%' % int(100.0 * sum_60 / sum_all),
                        'depth': avg_depth
                       }
        else:
            userdata = {'parther': '',
                        'time_all': sum_all,
                        'time_percent_3': sum_3,
                        'time_percent_15': sum_15,
                        'time_percent_30': sum_30,
                        'time_percent_60':sum_60,
                        'depth': avg_depth
                       }
            
        return h.jgridDataWrapper(table, userdata, page=page, 
                                  records_on_page=rows)


    def _get_data(self, domain, start_date, end_date, scope, relative):
        ''' Считает данные для таблицы статистики '''
        # Условия запроса к базе данных
        query_conditions =  {}
        query_conditions['domain'] = domain
        query_conditions['date'] = {"$gte": start_date, "$lte": end_date}
        if scope == 'partners':
            query_conditions['from_getmyad'] = True
        else:
            pass

        # Суммируем данные за период
        domain_by_reffer = {}
        for record in db.stat_per_date.find(query_conditions):

            if record['from_getmyad'] and scope == 'others':
                # (в отчёте по прочим сайтам все сайты-партнёры заменяются на
                # одну строчку getmyad.yottos.com)
                referrer = 'getmyad.yottos.com'
            else:
                referrer = record['referrer']
            key = referrer 
            value = domain_by_reffer.setdefault(key, {'3': 0,
                                                      '15': 0,
                                                      '30': 0,
                                                      '60': 0,
                                                      '3_rel': 0,
                                                      '15_rel': 0,
                                                      '30_rel': 0,
                                                      '60_rel': 0,
                                                      'depth': 0,
                                                      'total': 0})
            value['15'] += record['duration']['15'] + record['duration']['3']
            value['30'] += record['duration']['30']
            value['60'] += record['duration']['60']
            if scope == 'others':
                value['3'] = 0
            else:
                value['3'] += record.get('getmyad_clicks', 0) - record['duration']['3'] - \
                              record['duration']['15'] - record['duration']['30'] - \
                              record['duration']['60']
            if value['3'] < 0:
                value['3'] = 0
            value['depth'] += record['duration']['depth']

#        # Все неучтённые из GetMyAd клики считаем с глубиной просмотра 1
#        for item in domain_by_reffer.values():
#            item['depth'] += item['3'] * 1

        # При необходимости нормализуем
        precision = 0
        for referrer, value in domain_by_reffer.items():
            total = value['3'] + value['15'] + value['30'] + value['60']
            value['total'] = total

            if relative:
                value['3_rel'] = round(100.0 * value['3'] / total, precision)
                value['15_rel'] = round(100.0 * value['15'] / total, precision)
                value['30_rel'] = round(100.0 * value['30'] / total, precision)
                value['60_rel'] = round(100.0 * value['60'] / total, precision)
                
        return domain_by_reffer 


    def statcodeRequests(self):
        """Возвращает код, который должны разместить на своём сайте
           пользователи attractor '''
        """
        url  = request.params['url']
        url = base64.urlsafe_b64encode(url)        
        code = """
<script type="text/javascript"><!--
var yottos_id = "%s";
//-->
</script>
<script type="text/javascript" src="http://cdn.yottos.com/getmyad/yinfoe.js"></script>
        """ % url
        return code


    def hideUser(self):
        """ Скрывает пользователя из списка.

            Пользователь передаётся в get-параметре user """
        user = request.params.get('user', '')
        db.users.update({'id': user}, {'$set': {'hidden': True}}, safe=True)

