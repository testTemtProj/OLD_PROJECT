# This Python file uses the following encoding: utf-8
from datetime import datetime
from getmyad.lib.base import BaseController, render
from getmyad.model import StatisticReports
from pylons import request, response, session, tmpl_context as c, url, app_globals, config
from pylons.controllers.util import abort, redirect
from routes.util import url_for
import getmyad.lib.helpers as h
import getmyad.model as model
import json
import logging
import bson.json_util
import re
import time
from pprint import pprint
log = logging.getLogger(__name__)


def dateFromStr(str):
    try:
        day = int(str[0:2])
        month = int(str[3:5])
        year = int(str[6:10])
        return datetime(year, month, day)
    except:
        return None


class AdvertiseController(BaseController):

    def __before__(self, action, **params):
        user = session.get('user')
        if user:
            request.environ['CURRENT_USER'] = user
            request.environ['IS_MANAGER'] = session.get('isManager', False)

    def maker(self, id):
        if not session.get('user'):
            return redirect('/')

        if not id:
            return u"Не указан id выгрузки!"

        adv = app_globals.db.informer.find_one({'guid': id})

        if not adv:
            return u"Не найдена указанная выгрузка!"

        t = adv.get('admaker')
        c.admaker = h.JSON(t) if t else None
        c.adv_id = id
        c.track_attractor = adv.get('track_attractor', False)

        return render('/admaker.mako.html')

    def save(self):
        try:
            user = session.get('user')
            if not user:
                return h.JSON({'error': True, 'message': u'Не выполнен вход'})
            id = request.params.get('adv_id')
            object = json.loads(request.body)
            informer = model.Informer()
            informer.guid = id
            informer.user_login = user
            informer.admaker = object.get('options')
            informer.title = object.get('title')
            informer.domain = object.get('domain')
            informer.non_relevant = object.get('nonRelevant')
            informer.height = object.get('height')
            informer.width = object.get('width')
            informer.height_banner = object.get('height_banner')
            informer.width_banner = object.get('width_banner')
            #informer.auto_reload = 0 #object.get('auto_reload')
            informer.track_attractor = object.get('trackAttractor')

            informer.save()
            return h.JSON({'error': False, 'id': informer.guid})
        except Exception as ex:
            log.debug("Error in advertise.save(): " + str(ex))
            return h.JSON({'error': True, 'id': informer.guid,
                           'message': unicode(ex)})

    def showList(self):
        user = session.get('user')
        if not user:
            return "Login!"
        advertises = app_globals.db.informer.find().sort('user')
        data = [{'title': x['title'],
                 'guid': x['guid'],
                 'user': x['user']
                 } for x in advertises]
        return render('/advertiseList.mako.html', extra_vars={'data': data})

    def days(self, json=True):
        """ Возвращает разбитые по дням клики для каждой выгрузки текущего
            пользователя (для графиков).

            Формат: [{adv: {
                        guid: '...',
                        title: '...'
                      },
                      data: [[datestamp, clicks], [datestamp, clicks], ...],
                ...]
        """
        user = session.get('user')
        if not user:
            return ""

        result = []
        data = model.StatisticReport().statAdvByDate(user)
        for item in data:
            temp = {}
            for tmp in item['data']:
                temp[tmp[0]] = temp.get(tmp[0],0.0) + tmp[1]
            dateclick = [(int(time.mktime(key.timetuple()) * 1000),value) for key,value in temp.items()]
            dateclick.sort(key=lambda x: x[0])
            result.append({'adv': {'guid': item['guid'],
                                   'title': item['title'],
                                   'domain': item['domain']},
                           'data': dateclick
                           })

        return h.JSON(result) if json else result

    def domainsAdvertises(self):
        """ Возвращает выгрузки относящиеся к домену """
        user = session.get('user')
        domain = request.params.get('domain')
        advertises = self._domainsAdvertises(domain)

        return h.jgridDataWrapper(advertises)

    def _domainsAdvertises(self, domain):
        """ Возвращает выгрузки относящиеся к домену """
        if domain:
            advertises = [(x['title'], x['guid'])
                          for x in app_globals.db.informer.find({
                                     'user': session.get('user'),
                                     'domain': domain})]
        else:
            advertises = [(x['title'], x['guid'])
                          for x in app_globals.db.informer.find({
                                        'user': session.get('user'),
                                        'domain': {'$exists': False}})]
        return advertises

    def daysSummary(self):
        """Возвращает данные для таблицы суммарной статистики по дням """
        user = session.get('user')
        dateStart = dateFromStr(request.params.get('dateStart', None))
        dateEnd = dateFromStr(request.params.get('dateEnd', None))
        adv = request.params.get('adv')
        if user:
            from math import ceil
            try:
                page = int(request.params.get('page'))
                rows = int(request.params.get('rows'))
            except:
                page = 1
                rows = 10
            if not adv:
                data = model.StatisticReport().statUserGroupedByDate(
                                            user, dateStart, dateEnd)
            else:
                data = model.StatisticReport().statAdvGroupedByDate(
                                            adv, dateStart, dateEnd)
            data.sort(key=lambda x: x['date'])
            data.reverse()
            totalPages = int(ceil(float(len(data)) / rows))
            data = data[(page - 1) * rows: page * rows]
            data = [{'id': index,
                     'cell': (
                          "<b>%s</b>" % x['date'].strftime("%d.%m.%Y"),
                          x['impressions'],
                          x['unique'],
                          '%.3f%%' %
                            (round(x['unique'] * 100 / x['impressions'], 3)
                             if x['impressions'] else 0),
                          '%.2f $' %
                            (x['tiaser_totalCost'] / x['unique']) if x['unique'] else 0,
                          '%.2f $' % x['tiaser_totalCost'],
                          x['imp_banner_impressions'],
                          '%.2f $' %
                            (x['imp_banner_totalCost'] / (x['imp_banner_impressions']/1000)) if x['imp_banner_impressions'] else 0,
                          '%.2f $' % x['imp_banner_totalCost'],
                          x['banner_unique'],
                          '%.2f $' % (x['banner_totalCost'] / x['banner_unique']) if x['banner_unique'] else 0,
                          '%.2f $' % x['banner_totalCost'],
                          '%.2f $' % x['summ']
                        )
                     }
                    for index, x in enumerate(data)]
            return json.dumps({'total': totalPages,
                               'page': page,
                               'records': len(data),
                               'rows': data
                               },
                               default=bson.json_util.default,
                               ensure_ascii=False)
        else:
            return ""

    def allAdvertises(self, json=True):
        """ Суммарный отчёт по всем рекламным площадкам """
        user = session.get('user')
        dateStart = dateFromStr(request.params.get('dateStart', None))
        dateEnd = dateFromStr(request.params.get('dateEnd', None))

        reportData = model.StatisticReport().allAdvertiseScriptsSummary(user, dateStart, dateEnd)
        reportData.sort(cmp=lambda x, y: cmp(x['advTitle'], y['advTitle']),
                        key=None, reverse=False)
        data = [{'id': r['adv'],
                 'cell': [
                    r['advTitle'],
                    r['impressions'],
                    r['unique'],
                    '%.3f%%' % round(r['unique'] * 100 / r['impressions'], 3)
                               if r['impressions'] else 0,
                    '%.2f $' % round(r['tiaser_totalCost'] / r['unique'], 2)
                               if r['unique'] else 0,
                    '%.2f $' % round(r['tiaser_totalCost'], 2),
                    r['imp_banner_impressions'],
                    '%.2f $' % round(r['imp_banner_totalCost'] / (r['imp_banner_impressions']/1000), 2)
                               if (r['imp_banner_impressions'] and r['imp_banner_totalCost']) else 0,
                    '%.2f $' % round(r['imp_banner_totalCost'], 2),
                    r['banner_unique'],
                    '%.2f $' % round(r['banner_totalCost'] / r['banner_unique'], 2)
                               if r['banner_unique'] else 0,
                    '%.2f $' % round(r['banner_totalCost'], 2),
                    '%.2f $' % round(r['totalCost'], 2)
                 ]}
                for index, r in enumerate(reportData)]
        totalImpressions = sum([r['impressions']
                                for r in reportData if 'impressions' in r])
        totalUnique = sum([r['unique'] for r in reportData if 'unique' in r])
        bantotalUnique = sum([r['banner_unique'] for r in reportData if 'banner_unique' in r])
        totalTiaserSumm = sum([r['tiaser_totalCost']
                         for r in reportData if 'tiaser_totalCost' in r])
        totalTiaserCost = round(totalTiaserSumm / totalUnique, 2) if (totalUnique and totalTiaserSumm) else 0
        totalBannerImpressions = sum([r['banner_impressions']
                                for r in reportData if 'banner_impressions' in r])
        imptotalBannerSumm = sum([r['imp_banner_totalCost']
                         for r in reportData if 'imp_banner_totalCost' in r])
        totalBannerSumm = sum([r['banner_totalCost']
                         for r in reportData if 'banner_totalCost' in r])
        imptotalBannerCost = round(totalBannerSumm/(totalBannerImpressions/1000), 2) if (totalBannerImpressions and totalBannerSumm) else 0
        totalCost = sum([r['totalCost']
                         for r in reportData if 'totalCost' in r])
        totalBannerCost = round(totalBannerSumm / bantotalUnique, 2) if (bantotalUnique and totalBannerSumm) else 0

        result = {
            'total': len(data),
            'page': 1,
            'records': len(data),
            'rows': data,
            'userdata': {
                "Title": u"ИТОГО",
                "Impressions":    totalImpressions,
                "UniqueClicks":   totalUnique,
                "CTR_Unique":     '%.3f%%' % \
                            round(totalUnique * 100 / totalImpressions, 3) \
                            if totalImpressions else 0,
                "Cost":'%.2f $' % totalTiaserCost,
                "Summ":'%.2f $' % totalTiaserSumm,
                "imp_bannerImpressions":totalBannerImpressions,
                "imp_bannerCost":'%.2f $' % imptotalBannerCost,
                "imp_bannerSumm":'%.2f $' % imptotalBannerSumm,
                "banUniqueClicks":   bantotalUnique,
                "bannerCost":'%.2f $' % totalBannerCost,
                "bannerSumm":'%.2f $' % totalBannerSumm,
                "allSumm": '%.2f $' % totalCost
            }}

        return h.JSON(result) if json else result

    def create(self):
        """Создание выгрузки"""
        user = session.get('user')
        if not user:
            redirect(url_for(controller='main', action='index'))
        c.patterns = self._patterns()
        c.advertise = None
        c.domains = model.Account(login=user).domains()
        return render("/create_adv.mako.html")

    def edit(self):
        """Редактирование выгрузки"""
        user = session.get('user')
        if not user:
            redirect(url_for(controller='main', action='index'))
        guid = request.params.get('ads_id')
        x = app_globals.db.informer.find_one({'guid': guid})
        if not x:
            return u"Информер не найден!"

        advertise = {'title': x['title'],
                     'guid': x['guid'],
                     'options': x['admaker'],
                     'domain': x.get('domain', ''),
                     'auto_reload': x.get('auto_reload', 0),
                     'non_relevant': x.get('nonRelevant', {})
                    }
        from webhelpers.html.builder import escape as html_escape
        advertise['non_relevant']['userCode'] = unicode(html_escape(advertise['non_relevant'].get('userCode', '')))
        c.patterns = self._patterns() 
        c.advertise = advertise
        c.domains = model.Account(login=user).domains()
        return render("/create_adv.mako.html")

    def _patterns(self):
        """Возвращает образцы выгрузок"""
        return [{'title': x['title'],
                 'guid': x['guid'],
                 'options': x['admaker'],
                 'orient': x.get('orient'),
                 'popular': x.get('popular'),
                 'height':x.get('height'),
                 'width':x.get('width'),
                 'height_banner':x.get('height_baner'),
                 'width_banner':x.get('width_baner'),
                 'auto_reload': x.get('auto_reload', 60)}
                 for x in app_globals.db.informer.patterns.find({}).sort('title')]
