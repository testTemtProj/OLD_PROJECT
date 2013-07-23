# -*- coding: utf-8 -*-
from pprint import pprint

from datetime import datetime, date, time, timedelta
from formencode import Schema, validators as v
from getmyad import model
from getmyad.lib import helpers as h
from getmyad.lib.base import BaseController, render
from getmyad.model import Informer, Account, AccountReports, Permission, mq
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals, config
from pylons.controllers.util import abort, redirect
from routes.util import url_for
from uuid import uuid1
import formencode
import json
import logging
import os
import pymongo
from pymongo import DESCENDING, ASCENDING
import re
import base64
import uuid

import getmyad.tasks.mail as mail


def current_user_check(f):
    ''' Декоратор. Проверка есть ли в сессии авторизованный пользователь'''
    def wrapper(*args):
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()
        c.manager_login = user
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


log = logging.getLogger(__name__)

class ManagerController(BaseController):

    def __before__(self, action, **params):
        user = session.get('user')
        if user and session.get('isManager', False):
            c.user = user
            request.environ['CURRENT_USER'] = user
            request.environ['IS_MANAGER'] = True
        else:
            c.user = ''


    def index(self):
        """Кабинет менеджера"""
        if not c.user: 
            return redirect(url(controller="main", action="signOut"))
        
        token = str(uuid1()).upper()
        session[token] = {'user': session.get('user')}
        session.save()
        c.token = token      
        c.domainsRequests = self.domainsRequests()
        c.dataMoneyOutRequests = self.dataMoneyOutRequests()
        c.managersSummary = self.managersSummary()
        c.account = model.Account(login=c.user)
        c.account.load()
        c.permission = Permission(c.account)
        c.date = self.todayDateString()
        c.sum_out = self.sumOut() 
        c.prognoz_sum_out = '%.2f $' % self.prognozSumOut()
        c.notApprovedRequests = self.notApprovedActiveMoneyOutRequests()
        c.moneyOutHistory = self.moneyOutHistory()
        c.usersSummaryActualTime = self.usersSummaryActualTime()
        #log.info('Loggin user: %s ', c.user)
        
        return render("/manager.mako.html")
        
        
    def usersSummaryActualTime(self):
        ''' Время на которое актуальны данные статистики'''
        try:
            x = app_globals.db.config.find_one({'key': 'last stats_user_summary update'})
            actualTime = x.get('value')
            actualTime = actualTime.strftime('%H:%M %d.%m.%Y')
        except:
            actualTime = ''
        return actualTime
      
    def todayDateString(self): 
        monthNames = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
        now = datetime.today()
        return str(now.day) + ' ' + monthNames[now.month - 1] + ' ' + str(now.year) + ',  ' + str(now.time())[:8]
           
        
    def managersSummary(self):
        ''' Данные для таблицы данных о менеджерах'''
        ''' TODO в бд в поле blocked надо привести в единый вид и описать значения полей '''
        db = app_globals.db
        data = []
        for manager in db.users.find({"accountType": {'$in': ['manager', 'administrator']}}):
            if manager['accountType'] == 'manager':
                balance = model.ManagerReports(Account(manager['login'])).balance()
            else:
                balance = 0.0
            data.append((manager['login'], manager.get('percent', 0), "%.2f" % balance, manager.get('blocked', ''), manager['accountType']))
        return h.jgridDataWrapper(data)
    
    @current_user_check 
#    @expandtoken    
#    @authcheck    
    def overallSummaryByDays(self):
        ''' Данные для таблицы суммарных данных по дням ("Общая статистика") '''
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 15))
        sidx = request.params.get('sidx', 'date')
        sord = request.params.get('sord', 'desc')
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING
        queri = {}
        filds = {'geoClicks': False, 'geoClicksUnique': False, 'geoImpressions': False,'geoSocialClicks': False,\
                'geoSocialClicksUnique': False, 'geoSocialImpressions': False}
        count = app_globals.db.stats_daily_all.find(queri).count()
        if count > 0 and limit > 0:
            total_pages = int(count / limit)
        else:
            total_pages = 0;
        if page > total_pages:
            page = total_pages
        skip = (limit * page) - limit
        if skip < 0:
            skip = 0
        data = []
        cursor = app_globals.db.stats_daily_all.find(queri, filds).sort(sidx, sord).skip(skip).limit(limit)
        for x in cursor:
            date = x['date'].strftime("%d.%m.%Y")
            AccountSiteCount = str(x.get('acc_count', 0)) + "( " + str(x.get('act_acc_count', 0)) + "/" + str(x.get('domains_today', 0)) + " )"
            social_impressions_block = int(x.get('social_impressions_block', 0))
            social_clicks = int(x.get('social_clicks', 0))
            teaser_impressions_block = int(x.get('impressions_block', 0))
            teaser_clicksUnique = int(x.get('clicksUnique', 0))
            ctr_block = 100.0 * teaser_clicksUnique / teaser_impressions_block if (teaser_clicksUnique > 0 and teaser_impressions_block > 0) else 0
            teaser_totalCost = x.get('teaser_totalCost', 0)
            teaser_click_cost_avg = teaser_totalCost / teaser_clicksUnique if (teaser_clicksUnique > 0 and teaser_totalCost > 0) else 0
            imp_banner_impressions = int(x.get('imp_banner_impressions', 0))
            imp_banner_totalCost = x.get('imp_banner_totalCost', 0)
            imp_banner_click_cost_avg = (imp_banner_totalCost / (imp_banner_impressions / 1000.0)) if (imp_banner_totalCost > 0 and imp_banner_impressions > 0) else 0
            totalCost = x.get('totalCost', 0)
            row = (x['date'].weekday(),
                   date,
                   AccountSiteCount,
                   social_impressions_block,
                   social_clicks,
                   teaser_impressions_block,
                   teaser_clicksUnique,
                   '%.3f' % ctr_block,
                   h.formatMoney(teaser_totalCost),
                   '%.2f ¢' % (teaser_click_cost_avg * 100),
                   imp_banner_impressions,
                   '%.4f $' % imp_banner_click_cost_avg,
                   h.formatMoney(imp_banner_totalCost),
                   h.formatMoney(totalCost)
                   )
            data.append(row)
        return h.jgridDataWrapper(data, page = page, count = count, total_pages = total_pages)

    @current_user_check 
#    @expandtoken    
#    @authcheck    
    def overallTeaserSummaryByDays(self):
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 15))
        sidx = request.params.get('sidx', 'date')
        sord = request.params.get('sord', 'desc')
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING
        queri = {}
        filds = {'geoClicks': False, 'geoClicksUnique': False, 'geoImpressions': False,'geoSocialClicks': False,\
                'geoSocialClicksUnique': False, 'geoSocialImpressions': False}
        count = app_globals.db.stats_daily_all.find(queri).count()
        if count > 0 and limit > 0:
            total_pages = int(count / limit)
        else:
            total_pages = 0;
        if page > total_pages:
            page = total_pages
        skip = (limit * page) - limit
        if skip < 0:
            skip = 0
        data = []
        cursor = app_globals.db.stats_daily_all.find(queri, filds).sort(sidx, sord).skip(skip).limit(limit)
        for x in cursor:
            date = x['date'].strftime("%d.%m.%Y")
            AccountSiteCount = str(x.get('acc_count', 0)) + "( " + str(x.get('act_acc_count', 0)) + "/" + str(x.get('domains_today', 0)) + " )"
            teaser_impressions = int(x.get('impressions', 0))
            teaser_impressions_block = int(x.get('impressions_block', 0))
            teaser_clicks = int(x.get('clicks', 0))
            teaser_clicksUnique = int(x.get('clicksUnique', 0))
            ctr_block = 100.0 * teaser_clicksUnique / teaser_impressions_block if (teaser_clicksUnique > 0 and teaser_impressions_block > 0) else 0
            ctr = 100.0 * teaser_clicksUnique / teaser_impressions if (teaser_clicksUnique > 0 and teaser_impressions > 0) else 0
            teaser_totalCost = x.get('teaser_totalCost', 0)
            teaser_click_cost_avg = teaser_totalCost / teaser_clicksUnique if (teaser_clicksUnique > 0 and teaser_totalCost > 0) else 0
            row = (x['date'].weekday(),
                   date,
                   AccountSiteCount,
                   teaser_impressions,
                   teaser_impressions_block,
                   teaser_clicks,
                   teaser_clicksUnique,
                   h.formatMoney(teaser_totalCost),
                   '%.3f' % ctr,
                   '%.3f' % ctr_block,
                   '%.2f ¢' % (teaser_click_cost_avg * 100)
                   )
            data.append(row)
        return h.jgridDataWrapper(data, page = page, count = count, total_pages = total_pages)

    @current_user_check 
#    @expandtoken    
#    @authcheck    
    def overallBannerSummaryByDays(self):
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 15))
        sidx = request.params.get('sidx', 'date')
        sord = request.params.get('sord', 'desc')
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING
        queri = {}
        filds = {'geoClicks': False, 'geoClicksUnique': False, 'geoImpressions': False,'geoSocialClicks': False,\
                'geoSocialClicksUnique': False, 'geoSocialImpressions': False}
        count = app_globals.db.stats_daily_all.find(queri).count()
        if count > 0 and limit > 0:
            total_pages = int(count / limit)
        else:
            total_pages = 0;
        if page > total_pages:
            page = total_pages
        skip = (limit * page) - limit
        if skip < 0:
            skip = 0
        data = []
        cursor = app_globals.db.stats_daily_all.find(queri, filds).sort(sidx, sord).skip(skip).limit(limit)
        for x in cursor:
            date = x['date'].strftime("%d.%m.%Y")
            AccountSiteCount = str(x.get('acc_count', 0)) + "( " + str(x.get('act_acc_count', 0)) + "/" + str(x.get('domains_today', 0)) + " )"
            imp_banner_impressions = int(x.get('imp_banner_impressions', 0))
            imp_banner_clicksUnique = int(x.get('imp_banner_clicksUnique', 0))
            imp_banner_totalCost = x.get('imp_banner_totalCost', 0)
            imp_banner_click_cost_avg = (imp_banner_totalCost / (imp_banner_impressions / 1000.0)) if (imp_banner_totalCost > 0 and imp_banner_impressions > 0) else 0
            imp_ctr = 100.0 * imp_banner_clicksUnique / imp_banner_impressions if (imp_banner_clicksUnique > 0 and imp_banner_impressions > 0) else 0
            banner_impressions = int(x.get('banner_impressions', 0))
            banner_clicksUnique = int(x.get('banner_clicksUnique', 0))
            banner_totalCost = x.get('banner_totalCost', 0)
            banner_click_cost_avg = (banner_totalCost / (banner_impressions / 1000.0)) if (banner_totalCost > 0 and banner_impressions > 0) else 0
            ctr = 100.0 * banner_clicksUnique / banner_impressions if (banner_clicksUnique > 0 and banner_impressions > 0) else 0
            totalCost = imp_banner_totalCost + banner_totalCost
            row = (x['date'].weekday(),
                   date,
                   AccountSiteCount,
                   imp_banner_impressions,
                   imp_banner_clicksUnique,
                   '%.3f' % imp_ctr,
                   '%.4f $' % imp_banner_click_cost_avg,
                   h.formatMoney(imp_banner_totalCost),
                   banner_impressions,
                   banner_clicksUnique,
                   '%.3f' % ctr,
                   '%.4f $' % banner_click_cost_avg,
                   h.formatMoney(banner_totalCost),
                   h.formatMoney(totalCost)
                   )
            data.append(row)
        return h.jgridDataWrapper(data, page = page, count = count, total_pages = total_pages)

    def currentClickCost(self):
        """Отображает цену за клик для пользователя."""
        if not c.user:
            return h.userNotAuthorizedError()
        subgrid = request.params.get('subgrid', 'false')
        if subgrid == 'false':
            musers = self._usersList()
            filter_inactive = request.params.get('onlyActive', 'false') == 'true'
            if filter_inactive:
                users = [x.get('user') for x in
                        app_globals.db.stats_user_summary.find(
                            {'activity': 'greenflag'})]
            else:
                users = self._usersList()
            costs = app_globals.db.users.find({'login':{'$in':users}},{'login':1,'cost':1,'_id':0})
            data = []
            for item in costs:
                if item['login'] not in musers: continue
                click_percent = int(item.get('cost',{}).get('ALL',{}).get('click',{}).get('percent',50))
                click_cost_min = float(item.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_min',  0.01))
                click_cost_max = float(item.get('cost',{}).get('ALL',{}).get('click',{}).get('cost_max', 1.00))
                imp_percent = int(item.get('cost',{}).get('ALL',{}).get('imp',{}).get('percent',50))
                imp_cost_min = float(item.get('cost',{}).get('ALL',{}).get('imp',{}).get('cost_min',  0.05))
                imp_cost_max = float(item.get('cost',{}).get('ALL',{}).get('imp',{}).get('cost_max', 2.00))
                data.append((item.get('login',''),
                          click_percent,
                          click_cost_min,
                          click_cost_max,
                          imp_percent,
                          imp_cost_min,
                          imp_cost_max
                          ))
            return h.jgridDataWrapper(data, records_on_page = 20)
        else:
            id = request.params.get('id', '')
            account = model.Account(id)
            account.load()
            data = []
            for item in account.informers():
                guid = item.guid
                title = item.domain + ' ' + item.title
                if item.cost:
                    click_percent = int(item.cost.get('ALL',{}).get('click',{}).get('percent',50))
                    click_cost_min = float(item.cost.get('ALL',{}).get('click',{}).get('cost_min',  0.01))
                    click_cost_max = float(item.cost.get('ALL',{}).get('click',{}).get('cost_max', 1.00))
                    imp_percent = int(item.cost.get('ALL',{}).get('imp',{}).get('percent',50))
                    imp_cost_min = float(item.cost.get('ALL',{}).get('imp',{}).get('cost_min',  0.05))
                    imp_cost_max = float(item.cost.get('ALL',{}).get('imp',{}).get('cost_max', 2.00))
                else:
                    click_percent = request.params.get('click_percent', 50)
                    click_cost_min = request.params.get('click_cost_min', 0.01)
                    click_cost_max = request.params.get('click_cost_max', 1.00)
                    imp_percent = request.params.get('imp_percent',50)
                    imp_cost_min = request.params.get('imp_cost_min', 0.05)
                    imp_cost_max = request.params.get('imp_cost_max', 2.00)
                data.append((title,
                          click_percent,
                          click_cost_min,
                          click_cost_max,
                          imp_percent,
                          imp_cost_min,
                          imp_cost_max
                          ))
            return h.jgridDataWrapper(data, records_on_page = 20)
    
    def GeoSummaryByDays(self):
        ''' Данные для таблицы  о геопоказах по дням'''
        date = datetime.now()
        start_date = request.params.get('start_date', None)
        if start_date is not None and len(start_date) > 8:
            start_date = datetime.strptime(start_date, "%d.%m.%Y")
        else:
            start_date = datetime(date.year, date.month, date.day)
        get_country = request.params.get('country', None)
        queri = {'date': start_date}
        filds = {'date':True,
                 'geoClicks':True,
                 'geoClicksUnique':True,
                 'geoImpressions':True,
                 'geoSocialClicksUnique':True,
                 'geoSocialClicks':True,
                 'geoSocialImpressions':True}
        data = []
        geodata = app_globals.db.stats_overall_by_date.find_one(queri, filds)
        if not 'geoImpressions' in geodata:
            return h.jqGridLocalData(data,
                                 ['date', 'AccountSiteCount', 'social_impressions', 'social_clicks', 'impressions', 'clicks',
                                  'clicksUnique', 'bad_clicks', 'profit', 'ctr', 'click_cost'])
        if get_country:
            country = request.params.get('country', None)
            for item in geodata['geoImpressions']:
                if item == country:
                    for city in geodata['geoImpressions'][item][1]:
                        row = ( city,
                                geodata['geoImpressions'][item][1][city],
                                geodata['geoClicks'][item][1][city],
                                geodata['geoClicksUnique'][item][1][city],
                                geodata['geoSocialImpressions'][item][1][city],
                                geodata['geoSocialClicks'][item][1][city],
                                geodata['geoSocialClicksUnique'][item][1][city]
                                )
                        data.append(row)
        else:
            for item in geodata['geoImpressions']:
                row = ( item,
                        geodata['geoImpressions'][item][0],
                        geodata['geoClicks'][item][0],
                        geodata['geoClicksUnique'][item][0],
                        geodata['geoSocialImpressions'][item][0],
                        geodata['geoSocialClicks'][item][0],
                        geodata['geoSocialClicksUnique'][item][0]
                        )
                data.append(row)
        userdata = {}
        return  h.jgridDataWrapper(data, records_on_page = 20)
        
    def WorkerStats(self):
        ''' Данные для таблицы статистики работы воркера '''
        date = datetime.now()
        start_date = request.params.get('start_date', None)
        if start_date is not None and len(start_date) > 8:
            start_date = datetime.strptime(start_date, "%d.%m.%Y")
        else:
            start_date = datetime(date.year, date.month, date.day)
        queri = {'date': start_date}
        filds = {'date': False, '_id': False} 
        data = []
        workerstats = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsNM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsPM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsEM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsBM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsC = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsCNM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsCPM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsCEM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        workerstatsCBM = {'Банер по показам - Места размешения':0,
                       'Банер и Тизер по кликам - Места размешения':0,
                       'Банер и Тизер по кликам - Тематики':0,
                       'Банер по показам - Поисковый запрос':0,
                       'Банер по кликам - Поисковый запрос':0,
                       'Тизер по кликам - Поисковый запрос':0,
                       'Банер по показам - Контекст запрос':0,
                       'Банер по кликам - Контекст запрос':0,
                       'Тизер по кликам - Контекст запрос':0,
                       'Банер по показам - История поискового запроса':0,
                       'Банер по кликам - История поискового запроса':0,
                       'Тизер по кликам - История поискового запроса':0,
                       'Банер по показам - История контекстного запроса':0,
                       'Банер по кликам - История контекстного запроса':0,
                       'Тизер по кликам - История контекстного запроса':0,
                       'Банер по показам - История долгосрочная':0,
                       'Банер по кликам - История долгосрочная':0,
                       'Тизер по кликам - История долгосрочная':0,
                       'Вероятно сработала старая ветка':0,
                       'ИТОГО':0}
        stats = app_globals.db.worker_stats.find(queri, filds)
        for item in stats:
            for key, value in item.items():
                if key == 'L1':
                    workerstats['Банер по показам - Места размешения'] = workerstats.get('Банер по показам - Места размешения', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по показам - Места размешения'] = workerstatsNM.get('Банер по показам - Места размешения', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по показам - Места размешения'] = workerstatsPM.get('Банер по показам - Места размешения', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по показам - Места размешения'] = workerstatsEM.get('Банер по показам - Места размешения', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по показам - Места размешения'] = workerstatsBM.get('Банер по показам - Места размешения', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по показам - Места размешения'] = workerstatsC.get('Банер по показам - Места размешения', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по показам - Места размешения'] = workerstatsCNM.get('Банер по показам - Места размешения', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по показам - Места размешения'] = workerstatsCPM.get('Банер по показам - Места размешения', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по показам - Места размешения'] = workerstatsCEM.get('Банер по показам - Места размешения', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по показам - Места размешения'] = workerstatsCBM.get('Банер по показам - Места размешения', 0) + value.get('Cbroadmatch',0)
                elif key == 'L29':
                    workerstats['Банер и Тизер по кликам - Тематики'] = workerstats.get('Банер и Тизер по кликам - Тематики', 0) + value.get('ALL',0)
                    workerstatsNM['Банер и Тизер по кликам - Тематики'] = workerstatsNM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер и Тизер по кликам - Тематики'] = workerstatsPM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер и Тизер по кликам - Тематики'] = workerstatsEM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер и Тизер по кликам - Тематики'] = workerstatsBM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер и Тизер по кликам - Тематики'] = workerstatsC.get('Банер и Тизер по кликам - Тематики', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер и Тизер по кликам - Тематики'] = workerstatsCNM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер и Тизер по кликам - Тематики'] = workerstatsCPM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер и Тизер по кликам - Тематики'] = workerstatsCEM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер и Тизер по кликам - Тематики'] = workerstatsCBM.get('Банер и Тизер по кликам - Тематики', 0) + value.get('Cbroadmatch',0)
                elif key == 'L30':
                    workerstats['Банер и Тизер по кликам - Места размешения'] = workerstats.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('ALL',0)
                    workerstatsNM['Банер и Тизер по кликам - Места размешения'] = workerstatsNM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер и Тизер по кликам - Места размешения'] = workerstatsPM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер и Тизер по кликам - Места размешения'] = workerstatsEM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер и Тизер по кликам - Места размешения'] = workerstatsBM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер и Тизер по кликам - Места размешения'] = workerstatsC.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер и Тизер по кликам - Места размешения'] = workerstatsCNM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер и Тизер по кликам - Места размешения'] = workerstatsCPM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер и Тизер по кликам - Места размешения'] = workerstatsCEM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер и Тизер по кликам - Места размешения'] = workerstatsCBM.get('Банер и Тизер по кликам - Места размешения', 0) + value.get('Cbroadmatch',0)
                elif key == 'L2':
                    workerstats['Банер по показам - Поисковый запрос'] = workerstats.get('Банер по показам - Поисковый запрос', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по показам - Поисковый запрос'] = workerstatsNM.get('Банер по показам - Поисковый запрос', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по показам - Поисковый запрос'] = workerstatsPM.get('Банер по показам - Поисковый запрос', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по показам - Поисковый запрос'] = workerstatsEM.get('Банер по показам - Поисковый запрос', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по показам - Поисковый запрос'] = workerstatsBM.get('Банер по показам - Поисковый запрос', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по показам - Поисковый запрос'] = workerstatsC.get('Банер по показам - Поисковый запрос', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по показам - Поисковый запрос'] = workerstatsCNM.get('Банер по показам - Поисковый запрос', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по показам - Поисковый запрос'] = workerstatsCPM.get('Банер по показам - Поисковый запрос', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по показам - Поисковый запрос'] = workerstatsCEM.get('Банер по показам - Поисковый запрос', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по показам - Поисковый запрос'] = workerstatsCBM.get('Банер по показам - Поисковый запрос', 0) + value.get('Cbroadmatch',0)
                elif key == 'L7':
                    workerstats['Банер по кликам - Поисковый запрос'] = workerstats.get('Банер по кликам - Поисковый запрос', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по кликам - Поисковый запрос'] = workerstatsNM.get('Банер по кликам - Поисковый запрос', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по кликам - Поисковый запрос'] = workerstatsPM.get('Банер по кликам - Поисковый запрос', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по кликам - Поисковый запрос'] = workerstatsEM.get('Банер по кликам - Поисковый запрос', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по кликам - Поисковый запрос'] = workerstatsBM.get('Банер по кликам - Поисковый запрос', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по кликам - Поисковый запрос'] = workerstatsC.get('Банер по кликам - Поисковый запрос', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по кликам - Поисковый запрос'] = workerstatsCNM.get('Банер по кликам - Поисковый запрос', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по кликам - Поисковый запрос'] = workerstatsCPM.get('Банер по кликам - Поисковый запрос', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по кликам - Поисковый запрос'] = workerstatsCEM.get('Банер по кликам - Поисковый запрос', 0) + value.get('Cexactmatch',0)
                    workerstatsBM['Банер по кликам - Поисковый запрос'] = workerstatsCBM.get('Банер по кликам - Поисковый запрос', 0) + value.get('Cbroadmatch',0)
                elif key == 'L17':
                    workerstats['Тизер по кликам - Поисковый запрос'] = workerstats.get('Тизер по кликам - Поисковый запрос', 0) + value.get('ALL',0)
                    workerstatsNM['Тизер по кликам - Поисковый запрос'] = workerstatsNM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('nomatch',0)
                    workerstatsPM['Тизер по кликам - Поисковый запрос'] = workerstatsPM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('phrasematch',0)
                    workerstatsEM['Тизер по кликам - Поисковый запрос'] = workerstatsEM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('exactmatch',0)
                    workerstatsBM['Тизер по кликам - Поисковый запрос'] = workerstatsBM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('broadmatch',0)
                    workerstatsC['Тизер по кликам - Поисковый запрос'] = workerstatsC.get('Тизер по кликам - Поисковый запрос', 0) + value.get('CALL',0)
                    workerstatsCNM['Тизер по кликам - Поисковый запрос'] = workerstatsCNM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Тизер по кликам - Поисковый запрос'] = workerstatsCPM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Тизер по кликам - Поисковый запрос'] = workerstatsCEM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Тизер по кликам - Поисковый запрос'] = workerstatsCBM.get('Тизер по кликам - Поисковый запрос', 0) + value.get('Cbroadmatch',0)
                elif key == 'L3':
                    workerstats['Банер по показам - Контекст запрос'] = workerstats.get('Банер по показам - Контекст запрос', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по показам - Контекст запрос'] = workerstatsNM.get('Банер по показам - Контекст запрос', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по показам - Контекст запрос'] = workerstatsPM.get('Банер по показам - Контекст запрос', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по показам - Контекст запрос'] = workerstatsEM.get('Банер по показам - Контекст запрос', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по показам - Контекст запрос'] = workerstatsBM.get('Банер по показам - Контекст запрос', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по показам - Контекст запрос'] = workerstatsC.get('Банер по показам - Контекст запрос', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по показам - Контекст запрос'] = workerstatsCNM.get('Банер по показам - Контекст запрос', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по показам - Контекст запрос'] = workerstatsCPM.get('Банер по показам - Контекст запрос', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по показам - Контекст запрос'] = workerstatsCEM.get('Банер по показам - Контекст запрос', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по показам - Контекст запрос'] = workerstatsCBM.get('Банер по показам - Контекст запрос', 0) + value.get('Cbroadmatch',0)
                elif key == 'L8':
                    workerstats['Банер по кликам - Контекст запрос'] = workerstats.get('Банер по кликам - Контекст запрос', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по кликам - Контекст запрос'] = workerstatsNM.get('Банер по кликам - Контекст запрос', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по кликам - Контекст запрос'] = workerstatsPM.get('Банер по кликам - Контекст запрос', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по кликам - Контекст запрос'] = workerstatsEM.get('Банер по кликам - Контекст запрос', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по кликам - Контекст запрос'] = workerstatsBM.get('Банер по кликам - Контекст запрос', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по кликам - Контекст запрос'] = workerstatsC.get('Банер по кликам - Контекст запрос', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по кликам - Контекст запрос'] = workerstatsCNM.get('Банер по кликам - Контекст запрос', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по кликам - Контекст запрос'] = workerstatsCPM.get('Банер по кликам - Контекст запрос', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по кликам - Контекст запрос'] = workerstatsCEM.get('Банер по кликам - Контекст запрос', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по кликам - Контекст запрос'] = workerstatsCBM.get('Банер по кликам - Контекст запрос', 0) + value.get('Cbroadmatch',0)
                elif key == 'L18':
                    workerstats['Тизер по кликам - Контекст запрос'] = workerstats.get('Тизер по кликам - Контекст запрос', 0) + value.get('ALL',0)
                    workerstatsNM['Тизер по кликам - Контекст запрос'] = workerstatsNM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('nomatch',0)
                    workerstatsPM['Тизер по кликам - Контекст запрос'] = workerstatsPM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('phrasematch',0)
                    workerstatsEM['Тизер по кликам - Контекст запрос'] = workerstatsEM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('exactmatch',0)
                    workerstatsBM['Тизер по кликам - Контекст запрос'] = workerstatsBM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('broadmatch',0)
                    workerstatsC['Тизер по кликам - Контекст запрос'] = workerstatsC.get('Тизер по кликам - Контекст запрос', 0) + value.get('CALL',0)
                    workerstatsCNM['Тизер по кликам - Контекст запрос'] = workerstatsCNM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('Cnomatch',0)
                    workerstatsCPM['Тизер по кликам - Контекст запрос'] = workerstatsCPM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('Cphrasematch',0)
                    workerstatsCEM['Тизер по кликам - Контекст запрос'] = workerstatsCEM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('Cexactmatch',0)
                    workerstatsCBM['Тизер по кликам - Контекст запрос'] = workerstatsCBM.get('Тизер по кликам - Контекст запрос', 0) +  value.get('Cbroadmatch',0)
                elif key == 'L4':
                    workerstats['Банер по показам - История поискового запроса'] = workerstats.get('Банер по показам - История поискового запроса', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по показам - История поискового запроса'] = workerstatsNM.get('Банер по показам - История поискового запроса', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по показам - История поискового запроса'] = workerstatsPM.get('Банер по показам - История поискового запроса', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по показам - История поискового запроса'] = workerstatsEM.get('Банер по показам - История поискового запроса', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по показам - История поискового запроса'] = workerstatsBM.get('Банер по показам - История поискового запроса', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по показам - История поискового запроса'] = workerstatsC.get('Банер по показам - История поискового запроса', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по показам - История поискового запроса'] = workerstatsCNM.get('Банер по показам - История поискового запроса', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по показам - История поискового запроса'] = workerstatsCPM.get('Банер по показам - История поискового запроса', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по показам - История поискового запроса'] = workerstatsCEM.get('Банер по показам - История поискового запроса', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по показам - История поискового запроса'] = workerstatsCBM.get('Банер по показам - История поискового запроса', 0) + value.get('Cbroadmatch',0)
                elif key == 'L9':
                    workerstats['Банер по кликам - История поискового запроса'] = workerstats.get('Банер по кликам - История поискового запроса', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по кликам - История поискового запроса'] = workerstatsNM.get('Банер по кликам - История поискового запроса', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по кликам - История поискового запроса'] = workerstatsPM.get('Банер по кликам - История поискового запроса', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по кликам - История поискового запроса'] = workerstatsEM.get('Банер по кликам - История поискового запроса', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по кликам - История поискового запроса'] = workerstatsBM.get('Банер по кликам - История поискового запроса', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по кликам - История поискового запроса'] = workerstatsC.get('Банер по кликам - История поискового запроса', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по кликам - История поискового запроса'] = workerstatsCNM.get('Банер по кликам - История поискового запроса', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по кликам - История поискового запроса'] = workerstatsCPM.get('Банер по кликам - История поискового запроса', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по кликам - История поискового запроса'] = workerstatsCEM.get('Банер по кликам - История поискового запроса', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по кликам - История поискового запроса'] = workerstatsCBM.get('Банер по кликам - История поискового запроса', 0) + value.get('Cbroadmatch',0)
                elif key == 'L19':
                    workerstats['Тизер по кликам - История поискового запроса'] = workerstats.get('Тизер по кликам - История поискового запроса', 0) + value.get('ALL',0)
                    workerstatsNM['Тизер по кликам - История поискового запроса'] = workerstatsNM.get('Тизер по кликам - История поискового запроса', 0) + value.get('nomatch',0)
                    workerstatsPM['Тизер по кликам - История поискового запроса'] = workerstatsPM.get('Тизер по кликам - История поискового запроса', 0) + value.get('phrasematch',0)
                    workerstatsEM['Тизер по кликам - История поискового запроса'] = workerstatsEM.get('Тизер по кликам - История поискового запроса', 0) + value.get('exactmatch',0)
                    workerstatsBM['Тизер по кликам - История поискового запроса'] = workerstatsBM.get('Тизер по кликам - История поискового запроса', 0) + value.get('broadmatch',0)
                    workerstatsC['Тизер по кликам - История поискового запроса'] = workerstatsC.get('Тизер по кликам - История поискового запроса', 0) + value.get('CALL',0)
                    workerstatsCNM['Тизер по кликам - История поискового запроса'] = workerstatsCNM.get('Тизер по кликам - История поискового запроса', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Тизер по кликам - История поискового запроса'] = workerstatsCPM.get('Тизер по кликам - История поискового запроса', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Тизер по кликам - История поискового запроса'] = workerstatsCEM.get('Тизер по кликам - История поискового запроса', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Тизер по кликам - История поискового запроса'] = workerstatsCBM.get('Тизер по кликам - История поискового запроса', 0) + value.get('Cbroadmatch',0)
                elif key == 'L5':
                    workerstats['Банер по показам - История контекстного запроса'] = workerstats.get('Банер по показам - История контекстного запроса', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по показам - История контекстного запроса'] = workerstatsNM.get('Банер по показам - История контекстного запроса', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по показам - История контекстного запроса'] = workerstatsPM.get('Банер по показам - История контекстного запроса', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по показам - История контекстного запроса'] = workerstatsEM.get('Банер по показам - История контекстного запроса', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по показам - История контекстного запроса'] = workerstatsBM.get('Банер по показам - История контекстного запроса', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по показам - История контекстного запроса'] = workerstatsC.get('Банер по показам - История контекстного запроса', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по показам - История контекстного запроса'] = workerstatsCNM.get('Банер по показам - История контекстного запроса', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по показам - История контекстного запроса'] = workerstatsCPM.get('Банер по показам - История контекстного запроса', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по показам - История контекстного запроса'] = workerstatsCEM.get('Банер по показам - История контекстного запроса', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по показам - История контекстного запроса'] = workerstatsCBM.get('Банер по показам - История контекстного запроса', 0) + value.get('Cbroadmatch',0)
                elif key == 'L10':
                    workerstats['Банер по кликам - История контекстного запроса'] = workerstats.get('Банер по кликам - История контекстного запроса', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по кликам - История контекстного запроса'] = workerstatsNM.get('Банер по кликам - История контекстного запроса', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по кликам - История контекстного запроса'] = workerstatsPM.get('Банер по кликам - История контекстного запроса', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по кликам - История контекстного запроса'] = workerstatsEM.get('Банер по кликам - История контекстного запроса', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по кликам - История контекстного запроса'] = workerstatsBM.get('Банер по кликам - История контекстного запроса', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по кликам - История контекстного запроса'] = workerstatsC.get('Банер по кликам - История контекстного запроса', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по кликам - История контекстного запроса'] = workerstatsCNM.get('Банер по кликам - История контекстного запроса', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по кликам - История контекстного запроса'] = workerstatsCPM.get('Банер по кликам - История контекстного запроса', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по кликам - История контекстного запроса'] = workerstatsCEM.get('Банер по кликам - История контекстного запроса', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по кликам - История контекстного запроса'] = workerstatsCBM.get('Банер по кликам - История контекстного запроса', 0) + value.get('Cbroadmatch',0)
                elif key == 'L20':
                    workerstats['Тизер по кликам - История контекстного запроса'] = workerstats.get('Тизер по кликам - История контекстного запроса', 0) + value.get('ALL',0)
                    workerstatsNM['Тизер по кликам - История контекстного запроса'] = workerstatsNM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('nomatch',0)
                    workerstatsPM['Тизер по кликам - История контекстного запроса'] = workerstatsPM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('phrasematch',0)
                    workerstatsEM['Тизер по кликам - История контекстного запроса'] = workerstatsEM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('exactmatch',0)
                    workerstatsBM['Тизер по кликам - История контекстного запроса'] = workerstatsBM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('broadmatch',0)
                    workerstatsC['Тизер по кликам - История контекстного запроса'] = workerstatsC.get('Тизер по кликам - История контекстного запроса', 0) + value.get('CALL',0)
                    workerstatsCNM['Тизер по кликам - История контекстного запроса'] = workerstatsCNM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Тизер по кликам - История контекстного запроса'] = workerstatsCPM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Тизер по кликам - История контекстного запроса'] = workerstatsCEM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Тизер по кликам - История контекстного запроса'] = workerstatsCBM.get('Тизер по кликам - История контекстного запроса', 0) + value.get('Cbroadmatch',0)
                elif key == 'L6':
                    workerstats['Банер по показам - История долгосрочная'] = workerstats.get('Банер по показам - История долгосрочная', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по показам - История долгосрочная'] = workerstatsNM.get('Банер по показам - История долгосрочная', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по показам - История долгосрочная'] = workerstatsPM.get('Банер по показам - История долгосрочная', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по показам - История долгосрочная'] = workerstatsEM.get('Банер по показам - История долгосрочная', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по показам - История долгосрочная'] = workerstatsBM.get('Банер по показам - История долгосрочная', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по показам - История долгосрочная'] = workerstatsC.get('Банер по показам - История долгосрочная', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по показам - История долгосрочная'] = workerstatsCNM.get('Банер по показам - История долгосрочная', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по показам - История долгосрочная'] = workerstatsCPM.get('Банер по показам - История долгосрочная', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по показам - История долгосрочная'] = workerstatsCEM.get('Банер по показам - История долгосрочная', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по показам - История долгосрочная'] = workerstatsCBM.get('Банер по показам - История долгосрочная', 0) + value.get('Cbroadmatch',0)
                elif key == 'L11':
                    workerstats['Банер по кликам - История долгосрочная'] = workerstats.get('Банер по кликам - История долгосрочная', 0) + value.get('ALL',0)
                    workerstatsNM['Банер по кликам - История долгосрочная'] = workerstatsNM.get('Банер по кликам - История долгосрочная', 0) + value.get('nomatch',0)
                    workerstatsPM['Банер по кликам - История долгосрочная'] = workerstatsPM.get('Банер по кликам - История долгосрочная', 0) + value.get('phrasematch',0)
                    workerstatsEM['Банер по кликам - История долгосрочная'] = workerstatsEM.get('Банер по кликам - История долгосрочная', 0) + value.get('exactmatch',0)
                    workerstatsBM['Банер по кликам - История долгосрочная'] = workerstatsBM.get('Банер по кликам - История долгосрочная', 0) + value.get('broadmatch',0)
                    workerstatsC['Банер по кликам - История долгосрочная'] = workerstatsC.get('Банер по кликам - История долгосрочная', 0) + value.get('CALL',0)
                    workerstatsCNM['Банер по кликам - История долгосрочная'] = workerstatsCNM.get('Банер по кликам - История долгосрочная', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Банер по кликам - История долгосрочная'] = workerstatsCPM.get('Банер по кликам - История долгосрочная', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Банер по кликам - История долгосрочная'] = workerstatsCEM.get('Банер по кликам - История долгосрочная', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Банер по кликам - История долгосрочная'] = workerstatsCBM.get('Банер по кликам - История долгосрочная', 0) + value.get('Cbroadmatch',0)
                elif key == 'L21':
                    workerstats['Тизер по кликам - История долгосрочная'] = workerstats.get('Тизер по кликам - История долгосрочная', 0) + value.get('ALL',0)
                    workerstatsNM['Тизер по кликам - История долгосрочная'] = workerstatsNM.get('Тизер по кликам - История долгосрочная', 0) + value.get('nomatch',0)
                    workerstatsPM['Тизер по кликам - История долгосрочная'] = workerstatsPM.get('Тизер по кликам - История долгосрочная', 0) + value.get('phrasematch',0)
                    workerstatsEM['Тизер по кликам - История долгосрочная'] = workerstatsEM.get('Тизер по кликам - История долгосрочная', 0) + value.get('exactmatch',0)
                    workerstatsBM['Тизер по кликам - История долгосрочная'] = workerstatsBM.get('Тизер по кликам - История долгосрочная', 0) + value.get('broadmatch',0)
                    workerstatsC['Тизер по кликам - История долгосрочная'] = workerstatsC.get('Тизер по кликам - История долгосрочная', 0) + value.get('CALL',0)
                    workerstatsCNM['Тизер по кликам - История долгосрочная'] = workerstatsCNM.get('Тизер по кликам - История долгосрочная', 0) + value.get('Cnomatch',0)
                    workerstatsCPM['Тизер по кликам - История долгосрочная'] = workerstatsCPM.get('Тизер по кликам - История долгосрочная', 0) + value.get('Cphrasematch',0)
                    workerstatsCEM['Тизер по кликам - История долгосрочная'] = workerstatsCEM.get('Тизер по кликам - История долгосрочная', 0) + value.get('Cexactmatch',0)
                    workerstatsCBM['Тизер по кликам - История долгосрочная'] = workerstatsCBM.get('Тизер по кликам - История долгосрочная', 0) + value.get('Cbroadmatch',0)
                else:
                    workerstats['Вероятно сработала старая ветка'] = workerstats.get('Вероятно сработала старая ветка', 0) + value.get('ALL',0)
                    workerstatsC['Вероятно сработала старая ветка'] = workerstatsC.get('Вероятно сработала старая ветка', 0) + value.get('CALL',0)
                workerstats['ИТОГО'] = workerstats.get('ИТОГО', 0) + value.get('ALL',0)
                workerstatsC['ИТОГО'] = workerstatsC.get('ИТОГО', 0) + value.get('CALL',0)

        data.append(('Банер по показам - Места размешения',
            workerstats['Банер по показам - Места размешения'],
            workerstatsC['Банер по показам - Места размешения'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по показам - Места размешения'],
            workerstatsCNM['Банер по показам - Места размешения'],
            workerstatsBM['Банер по показам - Места размешения'],
            workerstatsCBM['Банер по показам - Места размешения'],
            workerstatsPM['Банер по показам - Места размешения'], 
            workerstatsCPM['Банер по показам - Места размешения'], 
            workerstatsEM['Банер по показам - Места размешения'],
            workerstatsCEM['Банер по показам - Места размешения']))
        data.append(('Банер и Тизер по кликам - Места размешения',
            workerstats['Банер и Тизер по кликам - Места размешения'],
            workerstatsC['Банер и Тизер по кликам - Места размешения'],
            "-", "-", "-", "-",
            workerstatsNM['Банер и Тизер по кликам - Места размешения'],
            workerstatsCNM['Банер и Тизер по кликам - Места размешения'],
            workerstatsBM['Банер и Тизер по кликам - Места размешения'], 
            workerstatsCBM['Банер и Тизер по кликам - Места размешения'], 
            workerstatsPM['Банер и Тизер по кликам - Места размешения'], 
            workerstatsCPM['Банер и Тизер по кликам - Места размешения'], 
            workerstatsEM['Банер и Тизер по кликам - Места размешения'],
            workerstatsCEM['Банер и Тизер по кликам - Места размешения']))
        data.append(('Банер и Тизер по кликам - Тематики',
            workerstats['Банер и Тизер по кликам - Тематики'],
            workerstatsC['Банер и Тизер по кликам - Тематики'],
            "-", "-", "-", "-",
            workerstatsNM['Банер и Тизер по кликам - Тематики'],
            workerstatsCNM['Банер и Тизер по кликам - Тематики'],
            workerstatsBM['Банер и Тизер по кликам - Тематики'], 
            workerstatsCBM['Банер и Тизер по кликам - Тематики'], 
            workerstatsPM['Банер и Тизер по кликам - Тематики'], 
            workerstatsCPM['Банер и Тизер по кликам - Тематики'], 
            workerstatsEM['Банер и Тизер по кликам - Тематики'],
            workerstatsCEM['Банер и Тизер по кликам - Тематики']))
        data.append(('Банер по показам - Поисковый запрос',
            workerstats['Банер по показам - Поисковый запрос'],
            workerstatsC['Банер по показам - Поисковый запрос'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по показам - Поисковый запрос'],
            workerstatsCNM['Банер по показам - Поисковый запрос'],
            workerstatsBM['Банер по показам - Поисковый запрос'], 
            workerstatsCBM['Банер по показам - Поисковый запрос'], 
            workerstatsPM['Банер по показам - Поисковый запрос'], 
            workerstatsCPM['Банер по показам - Поисковый запрос'], 
            workerstatsEM['Банер по показам - Поисковый запрос'],
            workerstatsCEM['Банер по показам - Поисковый запрос']))
        data.append(('Банер по кликам - Поисковый запрос',
            workerstats['Банер по кликам - Поисковый запрос'],
            workerstatsC['Банер по кликам - Поисковый запрос'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по кликам - Поисковый запрос'],
            workerstatsCNM['Банер по кликам - Поисковый запрос'],
            workerstatsBM['Банер по кликам - Поисковый запрос'], 
            workerstatsCBM['Банер по кликам - Поисковый запрос'], 
            workerstatsPM['Банер по кликам - Поисковый запрос'], 
            workerstatsCPM['Банер по кликам - Поисковый запрос'], 
            workerstatsEM['Банер по кликам - Поисковый запрос'],
            workerstatsCEM['Банер по кликам - Поисковый запрос']))
        data.append(('Тизер по кликам - Поисковый запрос',
            workerstats['Тизер по кликам - Поисковый запрос'],
            workerstatsC['Тизер по кликам - Поисковый запрос'],
            "-", "-", "-", "-",
            workerstatsNM['Тизер по кликам - Поисковый запрос'], 
            workerstatsCNM['Тизер по кликам - Поисковый запрос'], 
            workerstatsBM['Тизер по кликам - Поисковый запрос'], 
            workerstatsCBM['Тизер по кликам - Поисковый запрос'], 
            workerstatsPM['Тизер по кликам - Поисковый запрос'], 
            workerstatsCPM['Тизер по кликам - Поисковый запрос'], 
            workerstatsEM['Тизер по кликам - Поисковый запрос'],
            workerstatsCEM['Тизер по кликам - Поисковый запрос']))
        data.append(('Банер по показам - Контекст запрос',
            workerstats['Банер по показам - Контекст запрос'],
            workerstatsC['Банер по показам - Контекст запрос'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по показам - Контекст запрос'],
            workerstatsCNM['Банер по показам - Контекст запрос'],
            workerstatsBM['Банер по показам - Контекст запрос'],
            workerstatsCBM['Банер по показам - Контекст запрос'],
            workerstatsPM['Банер по показам - Контекст запрос'],
            workerstatsCPM['Банер по показам - Контекст запрос'],
            workerstatsEM['Банер по показам - Контекст запрос'],
            workerstatsCEM['Банер по показам - Контекст запрос']))
        data.append(('Банер по кликам - Контекст запрос',
            workerstats['Банер по кликам - Контекст запрос'],
            workerstatsC['Банер по кликам - Контекст запрос'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по кликам - Контекст запрос'],
            workerstatsCNM['Банер по кликам - Контекст запрос'],
            workerstatsBM['Банер по кликам - Контекст запрос'],
            workerstatsCBM['Банер по кликам - Контекст запрос'],
            workerstatsPM['Банер по кликам - Контекст запрос'],
            workerstatsCPM['Банер по кликам - Контекст запрос'],
            workerstatsEM['Банер по кликам - Контекст запрос'],
            workerstatsCEM['Банер по кликам - Контекст запрос']))
        data.append(('Тизер по кликам - Контекст запрос',
            workerstats['Тизер по кликам - Контекст запрос'],
            workerstatsC['Тизер по кликам - Контекст запрос'],
            "-", "-", "-", "-",
            workerstatsNM['Тизер по кликам - Контекст запрос'],
            workerstatsCNM['Тизер по кликам - Контекст запрос'],
            workerstatsBM['Тизер по кликам - Контекст запрос'], 
            workerstatsCBM['Тизер по кликам - Контекст запрос'], 
            workerstatsPM['Тизер по кликам - Контекст запрос'],
            workerstatsCPM['Тизер по кликам - Контекст запрос'],
            workerstatsEM['Тизер по кликам - Контекст запрос'],
            workerstatsCEM['Тизер по кликам - Контекст запрос']))
        data.append(('Банер по показам - История поискового запроса',
            workerstats['Банер по показам - История поискового запроса'],
            workerstatsC['Банер по показам - История поискового запроса'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по показам - История поискового запроса'],
            workerstatsCNM['Банер по показам - История поискового запроса'],
            workerstatsBM['Банер по показам - История поискового запроса'],
            workerstatsCBM['Банер по показам - История поискового запроса'],
            workerstatsPM['Банер по показам - История поискового запроса'],
            workerstatsCPM['Банер по показам - История поискового запроса'],
            workerstatsEM['Банер по показам - История поискового запроса'],
            workerstatsCEM['Банер по показам - История поискового запроса']))
        data.append(('Банер по кликам - История поискового запроса',
            workerstats['Банер по кликам - История поискового запроса'],
            workerstatsC['Банер по кликам - История поискового запроса'],
            "-", "-", "-", "-",
            workerstatsCNM['Банер по кликам - История поискового запроса'],
            workerstatsNM['Банер по кликам - История поискового запроса'],
            workerstatsCBM['Банер по кликам - История поискового запроса'],
            workerstatsBM['Банер по кликам - История поискового запроса'],
            workerstatsCPM['Банер по кликам - История поискового запроса'],
            workerstatsCPM['Банер по кликам - История поискового запроса'],
            workerstatsEM['Банер по кликам - История поискового запроса'],
            workerstatsCEM['Банер по кликам - История поискового запроса']))
        data.append(('Тизер по кликам - История поискового запроса',
            workerstats['Тизер по кликам - История поискового запроса'],
            workerstatsC['Тизер по кликам - История поискового запроса'],
            "-", "-", "-", "-",
            workerstatsNM['Тизер по кликам - История поискового запроса'],
            workerstatsCNM['Тизер по кликам - История поискового запроса'],
            workerstatsBM['Тизер по кликам - История поискового запроса'], 
            workerstatsCBM['Тизер по кликам - История поискового запроса'], 
            workerstatsPM['Тизер по кликам - История поискового запроса'], 
            workerstatsCPM['Тизер по кликам - История поискового запроса'], 
            workerstatsEM['Тизер по кликам - История поискового запроса'],
            workerstatsCEM['Тизер по кликам - История поискового запроса']))
        data.append(('Банер по показам - История контекстного запроса',
            workerstats['Банер по показам - История контекстного запроса'],
            workerstatsC['Банер по показам - История контекстного запроса'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по показам - История контекстного запроса'],
            workerstatsCNM['Банер по показам - История контекстного запроса'],
            workerstatsBM['Банер по показам - История контекстного запроса'],
            workerstatsCBM['Банер по показам - История контекстного запроса'],
            workerstatsPM['Банер по показам - История контекстного запроса'],
            workerstatsCPM['Банер по показам - История контекстного запроса'],
            workerstatsEM['Банер по показам - История контекстного запроса'],
            workerstatsCEM['Банер по показам - История контекстного запроса']))
        data.append(('Банер по кликам - История контекстного запроса',
            workerstats['Банер по кликам - История контекстного запроса'],
            workerstatsC['Банер по кликам - История контекстного запроса'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по кликам - История контекстного запроса'],
            workerstatsCNM['Банер по кликам - История контекстного запроса'],
            workerstatsBM['Банер по кликам - История контекстного запроса'],
            workerstatsCBM['Банер по кликам - История контекстного запроса'],
            workerstatsPM['Банер по кликам - История контекстного запроса'],
            workerstatsCPM['Банер по кликам - История контекстного запроса'],
            workerstatsEM['Банер по кликам - История контекстного запроса'],
            workerstatsCEM['Банер по кликам - История контекстного запроса']))
        data.append(('Тизер по кликам - История контекстного запроса',
            workerstats['Тизер по кликам - История контекстного запроса'],
            workerstatsC['Тизер по кликам - История контекстного запроса'],
            "-", "-", "-", "-",
            workerstatsNM['Тизер по кликам - История контекстного запроса'],
            workerstatsCNM['Тизер по кликам - История контекстного запроса'],
            workerstatsBM['Тизер по кликам - История контекстного запроса'],
            workerstatsCBM['Тизер по кликам - История контекстного запроса'],
            workerstatsPM['Тизер по кликам - История контекстного запроса'],
            workerstatsCPM['Тизер по кликам - История контекстного запроса'],
            workerstatsEM['Тизер по кликам - История контекстного запроса'],
            workerstatsCEM['Тизер по кликам - История контекстного запроса']))
        data.append(('Банер по показам - История долгосрочная',
            workerstats['Банер по показам - История долгосрочная'],
            workerstatsC['Банер по показам - История долгосрочная'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по показам - История долгосрочная'],
            workerstatsCNM['Банер по показам - История долгосрочная'],
            workerstatsBM['Банер по показам - История долгосрочная'],
            workerstatsCBM['Банер по показам - История долгосрочная'],
            workerstatsPM['Банер по показам - История долгосрочная'],
            workerstatsCPM['Банер по показам - История долгосрочная'],
            workerstatsEM['Банер по показам - История долгосрочная'],
            workerstatsCEM['Банер по показам - История долгосрочная']))
        data.append(('Банер по кликам - История долгосрочная',
            workerstats['Банер по кликам - История долгосрочная'],
            workerstatsC['Банер по кликам - История долгосрочная'],
            "-", "-", "-", "-",
            workerstatsNM['Банер по кликам - История долгосрочная'],
            workerstatsCNM['Банер по кликам - История долгосрочная'],
            workerstatsBM['Банер по кликам - История долгосрочная'],
            workerstatsCBM['Банер по кликам - История долгосрочная'],
            workerstatsPM['Банер по кликам - История долгосрочная'],
            workerstatsCPM['Банер по кликам - История долгосрочная'],
            workerstatsEM['Банер по кликам - История долгосрочная'],
            workerstatsCEM['Банер по кликам - История долгосрочная']))
        data.append(('Тизер по кликам - История долгосрочная',
            workerstats['Тизер по кликам - История долгосрочная'],
            workerstatsC['Тизер по кликам - История долгосрочная'],
            "-", "-", "-", "-",
            workerstatsNM['Тизер по кликам - История долгосрочная'],
            workerstatsCNM['Тизер по кликам - История долгосрочная'],
            workerstatsBM['Тизер по кликам - История долгосрочная'],
            workerstatsCBM['Тизер по кликам - История долгосрочная'],
            workerstatsPM['Тизер по кликам - История долгосрочная'],
            workerstatsCPM['Тизер по кликам - История долгосрочная'],
            workerstatsEM['Тизер по кликам - История долгосрочная'],
            workerstatsCEM['Тизер по кликам - История долгосрочная']))
        data.append(('Вероятно сработала старая ветка', workerstats['Вероятно сработала старая ветка'], workerstatsC['Вероятно сработала старая ветка'], "", "", "", "", "", "", "", "", "", "", ""))
        data.append(('ИТОГО', workerstats['ИТОГО'], workerstatsC['ИТОГО'], "", "", "", "", "", "", "", "", "", "", ""))
        return h.jgridDataWrapper(data)

    def GeoSummaryByUser(self):
        ''' Данные для таблицы  о геопоказах по дням и сайтам партнёрам'''
        date = datetime.now()
        start_date = request.params.get('start_date', None)
        if start_date is not None and len(start_date) > 8:
            start_date = datetime.strptime(start_date, "%d.%m.%Y")
        else:
            start_date = datetime(date.year, date.month, date.day)
        get_country = request.params.get('country', None)
        queri = {'date': start_date}
        filds = {'date':True,
                 'geoClicks':True,
                 'geoClicksUnique':True,
                 'geoImpressions':True,
                 'geoSocialClicksUnique':True,
                 'geoSocialClicks':True,
                 'geoSocialImpressions':True}
        data = []
        geodata = app_globals.db.stats_overall_by_date.find_one(queri, filds)
        if not 'geoImpressions' in geodata:
            return h.jqGridLocalData(data,
                                 ['date', 'AccountSiteCount', 'social_impressions', 'social_clicks', 'impressions', 'clicks',
                                  'clicksUnique', 'bad_clicks', 'profit', 'ctr', 'click_cost'])
        if get_country:
            country = request.params.get('country', None)
            for item in geodata['geoImpressions']:
                if item == country:
                    for city in geodata['geoImpressions'][item][1]:
                        row = ( city,
                                geodata['geoImpressions'][item][1][city],
                                geodata['geoClicks'][item][1][city],
                                geodata['geoClicksUnique'][item][1][city],
                                geodata['geoSocialImpressions'][item][1][city],
                                geodata['geoSocialClicks'][item][1][city],
                                geodata['geoSocialClicksUnique'][item][1][city]
                                )
                        data.append(row)
        else:
            for item in geodata['geoImpressions']:
                row = ( 1,
                        item,
                        geodata['geoImpressions'][item][0],
                        geodata['geoClicks'][item][0],
                        geodata['geoClicksUnique'][item][0],
                        geodata['geoSocialImpressions'][item][0],
                        geodata['geoSocialClicks'][item][0],
                        geodata['geoSocialClicksUnique'][item][0]
                        )
                data.append(row)
        userdata = {}
        return  h.jgridDataWrapper(data, records_on_page = 20)

    def rating(self):
        ''' Возвращает данные для js таблицы рейтинг товаров'''
        date = datetime.now()
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 20))
        sidx = request.params.get('sidx', 'title')
        sord = request.params.get('sord', 'asc')
        start_date = request.params.get('start_date', None)
        if start_date is not None and len(start_date) > 8:
            start_date = datetime.strptime(start_date, "%d.%m.%Y")
        else:
            start_date = datetime(date.year, date.month, date.day)
        end_date = request.params.get('end_date', None)
        if end_date is not None and len(end_date) > 8:
            end_date = datetime.strptime(end_date, "%d.%m.%Y")
        else:
            end_date = datetime(date.year, date.month, date.day) + timedelta(days=1)
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING 
        data = []
        queri = {}
        count = app_globals.db.offer.find(queri).count()
        if count > 0 and limit > 0:
            total_pages = int(count / limit)
        else:
            total_pages = 0;
        if page > total_pages:
            page = total_pages
        skip = (limit * page) - limit
        if skip < 0:
            skip = 0
        for offer in app_globals.db.offer.find(queri).skip(skip).limit(limit).sort(sidx, sord):
            full_impressions = offer.get('full_impressions', 0)
            full_clicks = offer.get('full_clicks', 0)
            impressions = offer.get('impressions', 0)
            clicks = offer.get('clicks', 0)
            old_impressions = offer.get('old_impressions', 0)
            old_clicks = offer.get('old_clicks', 0)
            full_ctr = 0
            ctr = 0
            old_ctr = 0
            if ((full_impressions > 0) and (full_clicks > 0)):
                full_ctr = (float(full_clicks) / full_impressions) * 100
            if ((old_impressions > 0) and (old_clicks > 0)):
                old_ctr = (float(old_clicks) / old_impressions) * 100
            if ((impressions > 0) and (clicks > 0)):
                ctr = (float(clicks) / impressions) * 100
            data.append((offer.get('title', 'no name'),
                        offer.get('campaignTitle', 'no name'),
                        offer.get('impressions', 0),
                        offer.get('clicks', 0),
                        ctr, 
                        offer.get('cost', 0),
                        offer.get('rating', 0),
                        offer.get('old_impressions', 0),
                        offer.get('old_clicks', 0),
                        old_ctr,
                        full_impressions,
                        full_clicks,
                        full_ctr))            
        return h.jgridDataWrapper(data, page = page, count = count, total_pages = total_pages)

    def ratingForInformers(self):
        ''' Возвращает данные для js таблицы рейтинг товаров'''
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 20))
        sidx = request.params.get('sidx', 'title')
        sord = request.params.get('sord', 'asc')
        get_subgrid = request.params.get('subgrid', None)
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING 
        data = []
        if get_subgrid:
            queri = {'adv': get_subgrid, 'rating':{'$exists':True}}
            for offer in app_globals.db.stats_daily.rating.find(queri):
                full_impressions = offer.get('full_impressions', 0)
                full_clicks = offer.get('full_clicks', 0)
                impressions = offer.get('impressions', 0)
                clicks = offer.get('clicks', 0)
                old_impressions = offer.get('old_impressions', 0)
                old_clicks = offer.get('old_clicks', 0)
                full_ctr = 0
                ctr = 0
                old_ctr = 0
                if ((full_impressions > 0) and (full_clicks > 0)):
                    full_ctr = (float(full_clicks) / full_impressions) * 100
                if ((old_impressions > 0) and (old_clicks > 0)):
                    old_ctr = (float(old_clicks) / old_impressions) * 100
                if ((impressions > 0) and (clicks > 0)):
                    ctr = (float(clicks) / impressions) * 100
                data.append((offer.get('title', 'no name'),
                            offer.get('campaignTitle', 'no name'),
                            offer.get('impressions', 0),
                            offer.get('clicks', 0),
                            ctr,
                            offer.get('cost', 0),
                            offer.get('rating', 0),
                            offer.get('old_impressions', 0),
                            offer.get('old_clicks', 0),
                            old_ctr,
                            full_impressions,
                            full_clicks,
                            full_ctr))         
        else:
            informers = app_globals.db.stats_daily.rating.group(
                                                                key = ['adv'],
                                                                condition = {'rating': {'$exists': True}},
                                                                reduce = '''function(o, p) {}''',
                                                                initial = {}
                                                                 )
            informersTitle = {}
            for item in app_globals.db.informer.find({},{'guid': True, 'domain': True, 'title': True}):
                informersTitle[item['guid']] = ' - '.join((item.get('domain', ''), item.get('title', '')))
            for item in informers:
                data.append((item['adv'],
                             informersTitle[item['adv']]
                            ))   
            data.sort(key=lambda x: x[1], reverse = False)
        return  h.jgridDataWrapper(data, records_on_page = 20)



    @current_user_check 
    @expandtoken    
    @authcheck    
    def setManagerPercent(self):
        """Устанавливает процент менеджера от дохода"""
        try:
            percent = float(request.params['percent'])
            manager_login = request.params['manager']
            if percent < 0 : raise
        except:
            return h.JSON({'error': True, 'msg': 'invalid arguments', 
                           'ok': False})
        model.setManagerPercent(manager_login, percent)
        return h.JSON({'error': False, 'ok': True})


    @current_user_check 
    @expandtoken    
    @authcheck    
    def block(self):
        """ Блокирует менеджера, логин которого передаётся в GET-параметре 
            ``manager`` """
        try:
            manager_login = request.params['manager']
            manager = model.Account(manager_login)
            manager.load()
            manager.blocked = 'banned'
            manager.update()
        except:
            return h.JSON({'error': True, 'ok': False})
        else:
            return h.JSON({'error': False, 'ok': True})


    def prognozSumOut(self):
        'Возвращает прогнозируемую сумму к выводу на ближайшее 10-е число'
        today = datetime.today()
        one_month = timedelta(days=30)
        if today.day > 10:
            month_day_10 = today + one_month
            month_day_10 = datetime(month_day_10.year, month_day_10.month, 10)
        else:
            month_day_10 = datetime(today.year, today.month, 10)
        daysdelta = month_day_10 - today

        calc_sum_out = 0
        for x in app_globals.db.stats_user_summary.find():
            try:
                avg_day_sum = float(x.get('totalCost_7', 0.0)) / 7
            except KeyError:
                avg_day_sum = 0
            account_delta = avg_day_sum * daysdelta.days
            account_sum = account_delta + x.get('summ', 0.0)
            try:
                data = app_globals.db.users.find_one({'login': x['login']})
                min_out_sum = float(data['min_out_sum'])
                prepayment = data.get('prepayment', False)
            except:
                min_out_sum = 100
                prepayment = False
            if account_sum >= min_out_sum or prepayment:
                calc_sum_out += account_sum
            
        return calc_sum_out


    def sumOut(self):
        """ Возвращает сумму доступную к выводу на сегодня с разбиением по 
            предполагаемым способам вывода.
        
            Способ вывода пытается определить на основании последнего
            использованного метода (хранится с поле lastPaymentType коллекции
            users). Если выводов ещё не было, то смотрит на доступные методы.
            Если доступен только один какой-либо, то приписывает сумму к нему.
            Если доступно более одного способа, относит сумму к неопределённым 
            методам ('unknown').            
            
            Возвращает структуру вида::
            
                { 'total': 100.0,        # Общая сумма к выводу
                  'webmoney_z': 50.0,    # \
                  'yandex': 50.0,
                  'card': 10.0,          #  > Сумма вывода каждым методом
                  'factura': 15.0,       # /
                  'unknown': 25.0        # Не удалось определить метод
                }
                
        """
        
        result = {'total': 0.0,
                  'webmoney_z': 0.0,
                  'yandex': 0.0,
                  'card': 0.0,
                  'factura': 0.0,
                  'unknown': 0.0}
        
        for x in app_globals.db.stats_user_summary.find():
            try:
                user_data = app_globals.db.users.find_one({'login': x['user']})
                min_out_sum = float(user_data['min_out_sum'])
                prepayment = user_data.get('prepayment', False)
            except (KeyError, ValueError, TypeError):
                min_out_sum = 100
                prepayment = False

            if user_data:
                if user_data.get('lastPaymentType'):
                    payment_type = user_data.get('lastPaymentType')
                elif len(user_data.get('moneyOutPaymentType', [])) == 1:
                    payment_type = user_data.get('moneyOutPaymentType')[0]
                elif not user_data.get('moneyOutPaymentType'):
                    payment_type = 'webmoney_z'
                else:
                    payment_type = 'unknown'
            else:
                payment_type = 'unknown'

            accountSumm = x.get('summ', 0)
            if prepayment or accountSumm >= min_out_sum:
                result[payment_type] += accountSumm
                result['total'] += accountSumm
        return result
    
    
    def tableForDataMoneyOutRequest(self, data_from_db):
        '''Возвращает форматированные данные для jgrid.

           На входе принимает результат запроса к db.money_out_request.

           Обращает внимание на get-параметры ``page`` и ``rows``, 
           которые нужны jqGrid для пейджинга.
           '''
        
        def commentFormat(str):
            ''' Форматирует строку вывода'''
            if not str: return ''
            str = str.replace('\n', ' ')
            res = ['']
            j = 0
            for sub in str.split(' '):
                if len(res[j] + sub + ' ') > 40:
                    res[j] += '\n'
                    j += 1
                    res.append('')
                res[j] += sub + ' '
            import string     
            return string.join(res)
        
        if not c.user: return h.userNotAuthorizedError()
        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
            return h.JSON(None)
        data = []
        for x in data_from_db:
            login = x['user']['login']
            date = x.get('date').strftime("%d.%m.%Y %H:%M")
            summ = '%.2f $' % x['summ']
            user_confirmed = u"Да" if x.get('user_confirmed') else u"Нет"    
            approved = u"Да" if x.get('approved', False) \
                             else u"<b style='color: red;'>Нет</b>"    
            manager_agreed = u"Да" if x.get('manager_agreed', False) \
                                   else u"<b style='color: red;'>Нет</b>"    
            phone = x.get('phone')   
            paymentType = u'счёт-фактура' if x.get('paymentType') == 'factura' else x.get('paymentType') 
             
            if x.get('paymentType') == 'webmoney_z': 
                comment = (u'<b>Логин Webmoney:</b> %s<br/>' + 
                           u'<b>Номер счёта Webmoney:</b> %s<br/>')% (x['webmoneyLogin'], x['webmoneyAccount'])
            elif x.get('paymentType') == 'card':
                comment = (u'<b>Банк:</b> %s <br/>' \
                           u'<b>Номер пластиковой карты:</b> %s<br/>' \
                           u'<b>Имя владельца карты:</b> %s <br/>' \
                           u'<b>Срок действия карты:</b> %s/%s <br/>' \
                           u'<b>Валюта и тип карты:</b> %s %s<br/>' \
                           u'<b>МФО банка:</b> %s <br/>' \
                           u'<b>ОКПО банка:</b> %s <br/>' \
                           u'<b>Транзитный счёт:</b> %s <br/>' \
                           ) \
                            % (x.get('bank'),
                               x.get('cardNumber'), 
                               x.get('cardName'), 
                               x.get('expire_month'),
                               x.get('expire_year'),
                               x.get('cardCurrency', ''),
                               x.get('cardType', ''),
                               x.get('bank_MFO', ''),
                               x.get('bank_OKPO', ''),
                               x.get('bank_TransitAccount', ''))
            elif x.get('paymentType') == 'factura':
                comment = (u'<b>Контакты:</b> %s<br/>' +
                           u'<a href="/manager/openSchetFacturaFile?filename=%s" class="facturaLink" target="_blank">' + 
                           u'Счёт-фактура</a><br/>') \
                           %(x.get('contact'),
                             x.get('schet_factura_file_name'))
            elif x.get('paymentType') == 'yandex':
                comment = (u'<b>Счёт Яндекс Деньги:</b> %s<br/>')% x['yandex_number']

            else:
                comment = u''                         

            if x.get('ip'):
                comment += u'<b>IP:</b> %s <br />' % x['ip']
            
            if x.get('comment'):
                comment += u'<b>Примечания:</b> %s ' % commentFormat(x['comment'])               

            protectionCode = x.get('protectionCode', '')
            protectionDate = x.get('protectionDate', '')
            protectionDate = protectionDate.strftime("%d.%m.%Y") if isinstance(protectionDate, datetime) else ''
            
            data.append((login, date, summ, user_confirmed, manager_agreed, 
                         approved, phone, paymentType, protectionCode, protectionDate, comment))                
        return h.jgridDataWrapper(data, 
                                  page=request.params.get('page', 1),
                                  records_on_page=request.params.get('rows', 10))
        

    def dataMoneyOutRequests(self):
        """Возвращает данные для таблицы со списком заявок на вывод средств"""
        data_from_db = app_globals.db.money_out_request.find().\
                                    sort('date', pymongo.DESCENDING)
        return self.tableForDataMoneyOutRequest(data_from_db)                            
        
    
    def notApprovedActiveMoneyOutRequests(self):
        ''' Количество неодобреных заявок на вывод средств'''
        count = 0
        today = datetime.today()
        three_days_ago = today - timedelta(days=3)
        for x in app_globals.db.money_out_request.group([],
                                    {'approved': {'$ne': True},
                                     'date': {'$gt': three_days_ago}},
                                    {'count': 0},
                                    'function(o,p) {p.count += 1};'):
            count = x['count']
        return str(int(count))
#        return h.JSON({'count': count})
    
    @current_user_check 
    @expandtoken    
    @authcheck 
    def approveMoneyOut(self):
        """Одобряет заявку пользователя user со временем date (передаются в параметрах)"""
        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
            return h.insufficientRightsError()
        
        user = request.params.get('user')
        date = h.datetimeFromStr(request.params.get('date'))
        t = request.params.get('approved', '').lower()
        if t == 'true':
            approved = True
        elif t == 'false':
            approved = False
        else:
            approved = '' 
        
        if not user or not date or not approved:
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        protectionCode = request.params.get('protectionCode', '')
        protectionPeriod = request.params.get('protectionPeriod', '')

        if len(protectionCode) and not protectionCode.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        if len(protectionPeriod) and not protectionPeriod.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        # Обновляем заявку
        db = app_globals.db
        money_out_request = \
            db.money_out_request.find_one({'user.login': user,
                                           'date': {'$gte': date,
                                                    '$lte': (date + timedelta(seconds=60))}})
        money_out_request['approved'] = approved

        if money_out_request['paymentType'] in ['webmoney_z', 'yandex']:
            money_out_request['protectionCode'] = protectionCode
            money_out_request['protectionDate'] = datetime.now() + timedelta(days=int(protectionPeriod)) if len(protectionPeriod) else ''

        db.money_out_request.save(money_out_request, safe=True)
        
        # Обновляем последний метод вывода средств для пользователя 
        db.users.update({'login': user},
                        {'$set': {'lastPaymentType': money_out_request.get('paymentType', '')}},
                        safe=True)

        user_account = Account(money_out_request['user']['login'])
        user_account.load()

        if money_out_request['paymentType']  == 'webmoney_z':
            try:
                mail.money_out_request.delay(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       wmid=money_out_request['webmoneyLogin'], \
                                       purse=money_out_request['webmoneyAccount'], \
                                       protection_code=money_out_request['protectionCode'], \
                                       code_expires=money_out_request['protectionDate'].strftime("%d.%m.%y %H:%M") \
                                                    if isinstance(money_out_request['protectionDate'], datetime) \
                                                    else money_out_request['protectionDate'])
            except Exception as ex:
                mail.money_out_request(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       wmid=money_out_request['webmoneyLogin'], \
                                       purse=money_out_request['webmoneyAccount'], \
                                       protection_code=money_out_request['protectionCode'], \
                                       code_expires=money_out_request['protectionDate'].strftime("%d.%m.%y %H:%M") \
                                                    if isinstance(money_out_request['protectionDate'], datetime) \
                                                    else money_out_request['protectionDate'])
        elif money_out_request['paymentType'] == 'card':
            try:
                mail.money_out_request.delay(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       bank_name=money_out_request['bank'], \
                                       card_number=money_out_request['cardNumber'], \
                                       card_name=money_out_request['cardName'], \
                                       card_expires='/'.join([money_out_request['expire_month'], money_out_request['expire_year']]), \
                                       card_currency_and_type=' '.join([money_out_request['cardCurrency'], money_out_request['cardType']]), \
                                       bank_mfo=money_out_request['bank_MFO'] if money_out_request['bank_MFO'] else '', \
                                       bank_okpo=money_out_request['bank_OKPO'] if money_out_request['bank_OKPO'] else '', \
                                       transit_account=money_out_request['bank_TransitAccount'] if money_out_request['bank_TransitAccount'] else '') 
            except Exception as ex:
                mail.money_out_request(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       bank_name=money_out_request['bank'], \
                                       card_number=money_out_request['cardNumber'], \
                                       card_name=money_out_request['cardName'], \
                                       card_expires='/'.join([money_out_request['expire_month'], money_out_request['expire_year']]), \
                                       card_currency_and_type=' '.join([money_out_request['cardCurrency'], money_out_request['cardType']]), \
                                       bank_mfo=money_out_request['bank_MFO'] if money_out_request['bank_MFO'] else '', \
                                       bank_okpo=money_out_request['bank_OKPO'] if money_out_request['bank_OKPO'] else '', \
                                       transit_account=money_out_request['bank_TransitAccount'] if money_out_request['bank_TransitAccount'] else '') 
        elif money_out_request['paymentType'] == 'factura':
            try:
                mail.money_out_request.delay(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       contact=money_out_request['contact'])
            except Exception as ex:
                mail.money_out_request(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       contact=money_out_request['contact'])
        elif money_out_request['paymentType'] == 'yandex':
            try:
                mail.money_out_request.delay(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       yandex_account=money_out_request['yandex_number'], \
                                       protection_code=money_out_request['protectionCode'], \
                                       code_expires=money_out_request['protectionDate'].strftime("%d.%m.%y %H:%M") \
                                                    if isinstance(money_out_request['protectionDate'], datetime) \
                                                    else money_out_request['protectionDate'])
            except Exception as ex:
                mail.money_out_request(money_out_request['paymentType'], user_account.email, \
                                       summ=money_out_request['summ'], \
                                       yandex_account=money_out_request['yandex_number'], \
                                       protection_code=money_out_request['protectionCode'], \
                                       code_expires=money_out_request['protectionDate'].strftime("%d.%m.%y %H:%M") \
                                                    if isinstance(money_out_request['protectionDate'], datetime) \
                                                    else money_out_request['protectionDate'])

        return json.dumps({'error': False, 'ok': True, 'date': date.strftime("%d.%m.%Y %H:%M"), 'date2': (date + timedelta(seconds=60)).strftime("%d.%m.%Y %H:%M")})


    @current_user_check 
    @expandtoken    
    @authcheck 
    def agreeMoneyOut(self):
        """ Разрешает заявку пользователя ``user`` со временем ``date``
            (передаются в GET-параметрах) """

        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
            return h.insufficientRightsError()
        
        user = request.params.get('user')
        date = h.datetimeFromStr(request.params.get('date'))
        t = request.params.get('approved', '').lower()
        if t == 'true':
            approved = True
        elif t == 'false':
            approved = False
        else:
            approved = '' 
        
        if not user or not date or not approved:
            return json.dumps({'error': True, 'msg': 'invalid arguments', 
                               'ok': False})

        # Обновляем заявку
        db = app_globals.db
        money_out_request = \
            db.money_out_request.find_one({'user.login': user,
                                           'date': {'$gte': date,
                                                    '$lte': (date + timedelta(seconds=60))}})
        money_out_request['manager_agreed'] = approved
        db.money_out_request.save(money_out_request, safe=True)
        
        return h.JSON({'error': False, 'ok': True,
                       'date': date.strftime("%d.%m.%Y %H:%M"),
                       'date2': (date + timedelta(seconds=60))\
                                        .strftime("%d.%m.%Y %H:%M")})

    
    def dataUserSocialImpressions(self):
        date = datetime.now()
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 20))
        sidx = request.params.get('sidx', 'domain')
        sord = request.params.get('sord', 'asc')
        start_date = request.params.get('start_date', None)
        if start_date is not None and len(start_date) > 8:
            start_date = datetime.strptime(start_date, "%d.%m.%Y")
        else:
            start_date = datetime(date.year, date.month, date.day)
        end_date = datetime(start_date.year, start_date.month, start_date.day) + timedelta(days=1)
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING
        queri = {'date':{'$gte': start_date, '$lt': end_date}}
        filds = {'date':True, 'domain':True,'social_clicks':True,'social_clicksUnique':True, 'social_impressions':True,'clicks':True, 'clicksUnique':True, 'impressions':True , 'ctr_social_impressions':True , 'ctr_impressions':True, 'ctr_difference_impressions': True}
        count = app_globals.db.stats_daily_domain.find(queri).count()
        if count > 0 and limit > 0:
            total_pages = int(count / limit)
        else:
            total_pages = 0;
        if page > total_pages:
            page = total_pages
        skip = (limit * page) - limit
        if skip < 0:
            skip = 0

        data = []
        social = app_globals.db.stats_daily_domain.find(queri, filds).skip(skip).limit(limit).sort(sidx, sord)
        for item in social:
            data.append((item.get('domain', 'NOT'),
                         item.get('social_impressions', 0),
                         item.get('impressions', 0),
                         item.get('social_clicks', 0),
                         item.get('social_clicksUnique', 0),
                         item.get('clicks', 0),
                         item.get('clicksUnique', 0),
                         "%.2f" % item.get('ctr_social_impressions', 0),
                         "%.2f" % item.get('ctr_impressions', 0),
                         "%.2f" % item.get('ctr_difference_impressions', 0)
                         ))

        return h.jgridDataWrapper(data, page = page, count = count, total_pages = total_pages)

    def dataUsersBadCliks(self):
        date = datetime.now()
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 20))
        sidx = request.params.get('sidx', 'domain')
        sord = request.params.get('sord', 'asc')
        start_date = request.params.get('start_date', None)
        if start_date is not None and len(start_date) > 8:
            start_date = datetime.strptime(start_date, "%d.%m.%Y")
        else:
            start_date = datetime(date.year, date.month, date.day)
        end_date = datetime(start_date.year, start_date.month, start_date.day) + timedelta(days=1)
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING
        queri = {'date':{'$gte': start_date, '$lt': end_date}}
        filds = {'date':True, 'domain':True,'blacklistIp':True,'badTokenIp':True, 'manyClicks':True}
        count = app_globals.db.stats_daily_domain.find(queri).count()
        if count > 0 and limit > 0:
            total_pages = int(count / limit)
        else:
            total_pages = 0;
        if page > total_pages:
            page = total_pages
        skip = (limit * page) - limit
        if skip < 0:
            skip = 0

        data = []
        badclick = app_globals.db.stats_daily_domain.find(queri, filds).skip(skip).limit(limit).sort(sidx, sord)
        for item in badclick:
            data.append((item.get('domain', 'NOT'),
                         item.get('badTokenIp', 0),
                         item.get('manyClicks', 0),
                         item.get('blacklistIp', 0)))

        return h.jgridDataWrapper(data, page = page, count = count, total_pages = total_pages)

    def dataUsersViewTimeCliks(self):
        date = datetime.now()
        page = int(request.params.get('page', 0))
        limit = int(request.params.get('rows', 20))
        sidx = request.params.get('sidx', 'domain')
        sord = request.params.get('sord', 'asc')
        start_date = request.params.get('start_date', None)
        if start_date is not None and len(start_date) > 8:
            start_date = datetime.strptime(start_date, "%d.%m.%Y")
        else:
            start_date = datetime(date.year, date.month, date.day)
        end_date = datetime(start_date.year, start_date.month, start_date.day) + timedelta(days=1)
        if sord == 'asc':
            sord = ASCENDING
        else:
            sord = DESCENDING
        queri = {'date':{'$gte': start_date, '$lt': end_date}}
        filds = {'date':True, 'domain':True,'clicks':True,'view_seconds':True, 'social_clicks':True}
        count = app_globals.db.stats_daily_domain.find(queri).count()
        if count > 0 and limit > 0:
            total_pages = int(count / limit)
        else:
            total_pages = 0;
        if page > total_pages:
            page = total_pages
        skip = (limit * page) - limit
        if skip < 0:
            skip = 0

        data = []
        badclick = app_globals.db.stats_daily_domain.find(queri, filds).skip(skip).limit(limit).sort(sidx, sord)
        for item in badclick:
            data.append((item.get('domain', 'NOT'),
                         item.get('clicks', 0),
                         item.get('view_seconds', 0),
                         item.get('Ip', 0),
                         item.get('Ip', 0),
                         item.get('social_clicks', 0),
                         item.get('view_seconds', 0),
                         item.get('Ip', 0),
                         item.get('Ip', 0)))

        return h.jgridDataWrapper(data, page = page, count = count, total_pages = total_pages)

    def dataUsersImpressions(self):
        """Суммарные данные по всем пользователям по количеству показов"""
        users = self._usersList()
        data = []
        totalImpToday = 0
        totalImpYesterday = 0
        totalImpBeforeYesterday = 0
        totalImpWeek = 0
        totalImpMonth = 0
        totalImpYear = 0
        totalImpToday_block = 0
        totalImpYesterday_block = 0
        totalImpBeforeYesterday_block = 0
        totalImpWeek_block = 0
        totalImpMonth_block = 0
        totalImpYear_block = 0
        for x in app_globals.db.stats_user_summary.find().sort('impressions_block',DESCENDING):
            if x['user'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"
            data.append(('<a href="javascript:;" class="%s" >%s</a>'%(link_class,x['user']),
                        x.get('impressions',0) + x.get('imp_banner_impressions',0) + x.get('banner_impressions',0),
                        x.get('impressions_block',0),
                        x.get('impressions_2',0) + x.get('imp_banner_impressions_2',0) + x.get('banner_impressions_2',0),
                        x.get('impressions_block_2',0),
                        x.get('impressions_3',0) + x.get('imp_banner_impressions_3',0) + x.get('banner_impressions_3',0),
                        x.get('impressions_block_3',0),
                        x.get('impressions_7',0) + x.get('imp_banner_impressions_7',0) + x.get('banner_impressions_7',0),
                        x.get('impressions_block_7',0),
                        x.get('impressions_30',0) + x.get('imp_banner_impressions_30',0) + x.get('banner_impressions_30',0),
                        x.get('impressions_block_30',0),
                        x.get('impressions_365',0) + x.get('imp_banner_impressions_365',0) + x.get('banner_impressions_365',0),
                        x.get('impressions_block_365',0),
                        2 if x['activity'] == "greenflag" else 1))
            totalImpToday += x.get('impressions',0) + x.get('imp_banner_impressions',0) + x.get('banner_impressions',0)
            totalImpToday_block += x.get('impressions_block',0)
            totalImpYesterday += x.get('impressions_2',0) + x.get('imp_banner_impressions_2',0) + x.get('banner_impressions_2',0)
            totalImpYesterday_block += x.get('impressions_block_2',0)
            totalImpBeforeYesterday += x.get('impressions_3',0) + x.get('imp_banner_impressions_3',0) + x.get('banner_impressions_3',0)
            totalImpBeforeYesterday_block += x.get('impressions_block_3',0)
            totalImpWeek += x.get('impressions_7',0) + x.get('imp_banner_impressions_7',0) + x.get('banner_impressions_7',0)
            totalImpWeek_block += x.get('impressions_block_7',0)
            totalImpMonth += x.get('impressions_30',0) + x.get('imp_banner_impressions_30',0) + x.get('banner_impressions_30',0)
            totalImpMonth_block += x.get('impressions_block_30',0)
            totalImpYear += x.get('impressions_365',0) + x.get('imp_banner_impressions_365',0) + x.get('banner_impressions_365',0)
            totalImpYear_block += x.get('impressions_block_365',0)
        userdata = {'user': u'ИТОГО:',
                    'impToday': totalImpToday,
                    'impToday_block': totalImpToday_block,
                    'impYesterday': totalImpYesterday,
                    'impYesterday_block': totalImpYesterday_block,
                    'impBeforeYesterday': totalImpBeforeYesterday,
                    'impBeforeYesterday_block': totalImpBeforeYesterday_block,
                    'impWeek': totalImpWeek,
                    'impWeek_block': totalImpWeek_block,
                    'impMonth': totalImpMonth,
                    'impMonth_block': totalImpMonth_block,
                    'impYear': totalImpYear,
                    'impYear_block': totalImpYear_block
                    }
        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
            data.sort(key=lambda x: x[iCol-1], reverse = r)        
        return h.jgridDataWrapper(data, userdata)

    def dataTeaserUsersImpressions(self):
        """Суммарные данные по всем пользователям по количеству показов"""
        users = self._usersList()
        data = []
        totalImpToday = 0
        totalImpYesterday = 0
        totalImpBeforeYesterday = 0
        totalImpWeek = 0
        totalImpMonth = 0
        totalImpYear = 0
        totalImpToday_block = 0
        totalImpYesterday_block = 0
        totalImpBeforeYesterday_block = 0
        totalImpWeek_block = 0
        totalImpMonth_block = 0
        totalImpYear_block = 0
        for x in app_globals.db.stats_user_summary.find().sort('impressions',DESCENDING):
            if x['user'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"
            data.append(('<a href="javascript:;" class="%s" >%s</a>'%(link_class,x['user']),
                        x.get('impressions',0),
                        x.get('impressions_block',0) - x.get('imp_banner_impressions',0) - x.get('banner_impressions',0),
                        x.get('impressions_2',0),
                        x.get('impressions_block_2',0) - x.get('imp_banner_impressions_2',0) - x.get('banner_impressions_2',0),
                        x.get('impressions_3',0),
                        x.get('impressions_block_3',0) - x.get('imp_banner_impressions_3',0) - x.get('banner_impressions_3',0),
                        x.get('impressions_7',0),
                        x.get('impressions_block_7',0) - x.get('imp_banner_impressions_7',0) - x.get('banner_impressions_7',0),
                        x.get('impressions_30',0),
                        x.get('impressions_block_30',0) - x.get('imp_banner_impressions_30',0) - x.get('banner_impressions_30',0),
                        x.get('impressions_365',0),
                        x.get('impressions_block_365',0) - x.get('imp_banner_impressions_365',0) - x.get('banner_impressions_365',0),
                        2 if x['activity'] == "greenflag" else 1))
            totalImpToday += x.get('impressions',0)
            totalImpToday_block += x.get('impressions_block',0) - x.get('imp_banner_impressions',0) - x.get('banner_impressions',0)
            totalImpYesterday += x.get('impressions_2',0)
            totalImpYesterday_block += x.get('impressions_block_2',0) - x.get('imp_banner_impressions_2',0) - x.get('banner_impressions_2',0)
            totalImpBeforeYesterday += x.get('impressions_3',0)
            totalImpBeforeYesterday_block += x.get('impressions_block_3',0) - x.get('imp_banner_impressions_3',0) - x.get('banner_impressions_3',0)
            totalImpWeek += x.get('impressions_7',0)
            totalImpWeek_block += x.get('impressions_block_7',0) - x.get('imp_banner_impressions_7',0) - x.get('banner_impressions_7',0)
            totalImpMonth += x.get('impressions_30',0)
            totalImpMonth_block += x.get('impressions_block_30',0) - x.get('imp_banner_impressions_30',0) - x.get('banner_impressions_30',0)
            totalImpYear += x.get('impressions_365',0)
            totalImpYear_block += x.get('impressions_block_365',0) - x.get('imp_banner_impressions_365',0) - x.get('banner_impressions_365',0)
        userdata = {'user': u'ИТОГО:',
                    'impToday': totalImpToday,
                    'impToday_block': totalImpToday_block,
                    'impYesterday': totalImpYesterday,
                    'impYesterday_block': totalImpYesterday_block,
                    'impBeforeYesterday': totalImpBeforeYesterday,
                    'impBeforeYesterday_block': totalImpBeforeYesterday_block,
                    'impWeek': totalImpWeek,
                    'impWeek_block': totalImpWeek_block,
                    'impMonth': totalImpMonth,
                    'impMonth_block': totalImpMonth_block,
                    'impYear': totalImpYear,
                    'impYear_block': totalImpYear_block
                    }
        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
            data.sort(key=lambda x: x[iCol-1], reverse = r)        
        return h.jgridDataWrapper(data, userdata)



    def _is_yellow_star(self, user_summary):
        """Возвращает True, если пользователь подключился в течении последних
        суток. Такие пользователи подсвечиваются жёлтой звездочкой.

        Поскольку точно расчитать активность пользователя за последние 24 часа
        не возможно, применяется следующий алгоритм:

        1. Если текущее время меньше 12 часов, смотрим активность за текущий и
           два последних календарных дня.

        2. Если текущее время больше 12 часов, смотрим активность за текущий и
           вчерашний календарный день.

        ``user_summary``
            Структура из коллекции ``user.summary_per_date``.
        """
        now = datetime.now()
        active_today = user_summary.get('activity') == 'greenflag'
        active_yday = user_summary.get('activity_yesterday') == 'greenflag'
        active_before_yday = user_summary.get('activity_before_yesterday') == 'greenflag'

        if now.hour < 12:
            result = (active_today or active_yday) and not active_before_yday

        else:
            result = active_today and not active_yday

        return result


    def dataUsersSummary(self):
        """Суммарные данные по всем пользователям"""
        users = self._usersList()
        data = []
        totalSumm = 0
        totalSummMinus = 0
        totalSummToday = 0
        totalSummYesterday = 0
        totalSummBeforeYesterday = 0
        totalSummWeek = 0
        totalSummMonth = 0
        totalSummYear = 0

        for x in app_globals.db.stats_user_summary.find().sort('registrationDate'):
            if x['user'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"
            data.append(('<a href="javascript:;" class="%s" >%s</a>' % (link_class, x['user']),
                        h.formatMoney(x.get('totalCost',0)),
                        h.formatMoney(x.get('totalCost_2',0)),
                        h.formatMoney(x.get('totalCost_3',0)),
                        h.formatMoney(x.get('totalCost_7',0)),
                        h.formatMoney(x.get('totalCost_30',0)),
                        h.formatMoney(x.get('totalCost_365',0)),
                        h.formatMoney(x.get('summ',0)),
                        2 if x['activity'] == "greenflag" else 1))
            if x.get('summ',0) >= 0:
                totalSumm += x.get('summ',0)
            else: 
                totalSummMinus += x.get('summ',0) * (-1)    
            totalSummToday += x.get('totalCost',0)
            totalSummYesterday += x.get('totalCost_2',0)
            totalSummBeforeYesterday += x.get('totalCost_3',0)
            totalSummWeek += x.get('totalCost_7',0)
            totalSummMonth += x.get('totalCost_30',0)
            totalSummYear += x.get('totalCost_365',0)
            
        userdata = {'user': u'ИТОГО:',
                    'summ': h.formatMoney(totalSumm) + ", -" + h.formatMoney(totalSummMinus),
                    'summToday': h.formatMoney(totalSummToday),
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'summBeforeYesterday': h.formatMoney(totalSummBeforeYesterday),
                    'summWeek': h.formatMoney(totalSummWeek),
                    'summMonth': h.formatMoney(totalSummMonth),
                    'summYear': h.formatMoney(totalSummYear),
                   }

        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
            if iCol >= 2:
                data.sort(key=lambda x: float(str(x[iCol-1].partition(' ')[0])), reverse = r)
            else:
                data.sort(key=lambda x: x[iCol-1], reverse = r)        

        return h.jgridDataWrapper(data, userdata)

    def dataTeaserUsersSummary(self):
        """Суммарные данные по всем пользователям"""
        users = self._usersList()
        data = []
        totalSumm = 0
        totalSummMinus = 0
        totalSummToday = 0
        totalSummYesterday = 0
        totalSummBeforeYesterday = 0
        totalSummWeek = 0
        totalSummMonth = 0
        totalSummYear = 0

        for x in app_globals.db.stats_user_summary.find().sort('registrationDate'):
            if x['user'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"

            teaser_click_cost_avg = x.get('teaser_totalCost',0) / x.get('clicksUnique',0) if (x.get('teaser_totalCost',0) > 0 and x.get('clicksUnique',0) > 0) else 0
            teaser_click_cost_avg2 = x.get('teaser_totalCost_2',0) / x.get('clicksUnique_2',0) if (x.get('teaser_totalCost_2',0) > 0 and x.get('clicksUnique_2',0) > 0) else 0
            teaser_click_cost_avg7 = x.get('teaser_totalCost_7',0) / x.get('clicksUnique_7',0) if (x.get('teaser_totalCost_7',0) > 0 and x.get('clicksUnique_7',0) > 0) else 0
            i = x.get('impressions',0)
            ib =x.get('impressions_block',0) - x.get('imp_banner_impressions',0) - x.get('banner_impressions',0)
            i2 = x.get('impressions_2',0)
            ib2 = x.get('impressions_block_2',0) - x.get('imp_banner_impressions_2',0) - x.get('banner_impressions_2',0)
            i7 = x.get('impressions_7',0)
            ib7 = x.get('impressions_block_7',0) - x.get('imp_banner_impressions_7',0) - x.get('banner_impressions_7',0)
            data.append(('<a href="javascript:;" class="%s" >%s</a>' % (link_class, x['user']),
                        h.formatMoney(x.get('teaser_totalCost',0)),
                        h.formatMoney(x.get('teaser_totalCost_2',0)),
                        h.formatMoney(x.get('teaser_totalCost_3',0)),
                        h.formatMoney(x.get('teaser_totalCost_7',0)),
                        h.formatMoney(x.get('teaser_totalCost_30',0)),
                        h.formatMoney(x.get('teaser_totalCost_365',0)),
                        '%.2f c' % (teaser_click_cost_avg * 100),
                        '%.2f c' % (teaser_click_cost_avg2 * 100),
                        '%.2f c' % (teaser_click_cost_avg7 * 100),
                        '%.3f' % (((x.get('clicksUnique',0) / ib) * 100) if (x.get('clicksUnique',0) > 0 and ib > 0) else 0),
                        '%.3f' % (((x.get('clicksUnique_2',0) / ib2) * 100) if (x.get('clicksUnique_2',0) > 0 and ib2 > 0) else 0),
                        '%.3f' % (((x.get('clicksUnique_7',0) / ib7) * 100) if (x.get('clicksUnique_7',0) > 0 and ib7 > 0) else 0),
                        '%.3f' % (((x.get('clicksUnique',0) / i) * 100) if (x.get('clicksUnique',0) > 0 and i > 0) else 0),
                        '%.3f' % (((x.get('clicksUnique_2',0) / i2) * 100) if (x.get('clicksUnique_2',0) > 0 and i2 > 0) else 0),
                        '%.3f' % (((x.get('clicksUnique_7',0) / i7) * 100) if (x.get('clicksUnique_7',0) > 0 and i7 > 0) else 0),
                        2 if x['activity'] == "greenflag" else 1))
                        
            totalSummToday += x.get('teaser_totalCost',0)
            totalSummYesterday += x.get('teaser_totalCost_2',0)
            totalSummBeforeYesterday += x.get('teaser_totalCost_3',0)
            totalSummWeek += x.get('teaser_totalCost_7',0)
            totalSummMonth += x.get('teaser_totalCost_30',0)
            totalSummYear += x.get('teaser_totalCost_365',0)
            
        userdata = {'user': u'ИТОГО:',
                    'summToday': h.formatMoney(totalSummToday),
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'summBeforeYesterday': h.formatMoney(totalSummBeforeYesterday),
                    'summWeek': h.formatMoney(totalSummWeek),
                    'summMonth': h.formatMoney(totalSummMonth),
                    'summYear': h.formatMoney(totalSummYear)
                   }
        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
            if iCol >= 2:
                data.sort(key=lambda x: float(str(x[iCol-1].partition(' ')[0])), reverse = r)
            else:
                data.sort(key=lambda x: x[iCol-1], reverse = r)        

        return h.jgridDataWrapper(data, userdata)

    def dataBannerUsersSummary(self):
        """Суммарные данные по всем пользователям"""
        users = self._usersList()
        data = []
        totalSummToday = 0
        totalSummYesterday = 0
        totalSummBeforeYesterday = 0
        totalSummWeek = 0
        totalSummMonth = 0
        totalSummYear = 0
        for x in app_globals.db.stats_user_summary.find().sort('registrationDate'):
            if x['user'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"
            data.append(('<a href="javascript:;" class="%s" >%s</a>' % (link_class, x['user']),
                        h.formatMoney(x.get('banner_totalCost',0) + x.get('imp_banner_totalCost',0)),
                        h.formatMoney(x.get('banner_totalCost_2',0) + x.get('imp_banner_totalCost_2',0)),
                        h.formatMoney(x.get('banner_totalCost_3',0) + x.get('imp_banner_totalCost_3',0)),
                        h.formatMoney(x.get('banner_totalCost_7',0) + x.get('imp_banner_totalCost_7',0)),
                        h.formatMoney(x.get('banner_totalCost_30',0) + x.get('imp_banner_totalCost_30',0)),
                        h.formatMoney(x.get('banner_totalCost_365',0) + x.get('imp_banner_totalCost_365',0)),
                        2 if x['activity'] == "greenflag" else 1))
                    
            totalSummToday += (x.get('banner_totalCost',0) + x.get('imp_banner_totalCost',0))
            totalSummYesterday += (x.get('banner_totalCost_2',0) + x.get('imp_banner_totalCost_2',0))
            totalSummBeforeYesterday += (x.get('banner_totalCost_3',0) + x.get('imp_banner_totalCost_3',0))
            totalSummWeek += (x.get('banner_totalCost_7',0) + x.get('imp_banner_totalCost_7',0))
            totalSummMonth += (x.get('banner_totalCost_30',0) + x.get('imp_banner_totalCost_30',0))
            totalSummYear += (x.get('banner_totalCost_365',0) + x.get('imp_banner_totalCost_365',0))

            
        userdata = {'user': u'ИТОГО:',
                    'summToday': h.formatMoney(totalSummToday),
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'summBeforeYesterday': h.formatMoney(totalSummBeforeYesterday),
                    'summWeek': h.formatMoney(totalSummWeek),
                    'summMonth': h.formatMoney(totalSummMonth),
                    'summYear': h.formatMoney(totalSummYear)
                   }
        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
            if iCol >= 2:
                data.sort(key=lambda x: float(str(x[iCol-1].partition(' ')[0])), reverse = r)
            else:
                data.sort(key=lambda x: x[iCol-1], reverse = r)        

        return h.jgridDataWrapper(data, userdata)


    def dataBannerUsersImp(self):
        """Суммарные данные по всем пользователям"""
        users = self._usersList()
        data = []
        totalSummToday = 0
        totalSummYesterday = 0
        totalSummBeforeYesterday = 0
        totalSummWeek = 0
        totalSummMonth = 0
        totalSummYear = 0
        totalImpToday = 0
        totalImpYesterday = 0
        totalImpBeforeYesterday = 0
        totalImpWeek = 0
        totalImpMonth = 0
        totalImpYear = 0
        for x in app_globals.db.stats_user_summary.find().sort('registrationDate'):
            if x['user'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"
            data.append(('<a href="javascript:;" class="%s" >%s</a>' % (link_class, x['user']),
                        x.get('imp_banner_impressions',0),
                        h.formatMoney(x.get('imp_banner_totalCost',0)),
                        x.get('imp_banner_impressions_2',0),
                        h.formatMoney(x.get('imp_banner_totalCost_2',0)),
                        x.get('imp_banner_impressions_3',0),
                        h.formatMoney(x.get('imp_banner_totalCost_3',0)),
                        x.get('imp_banner_impressions_7',0),
                        h.formatMoney(x.get('imp_banner_totalCost_7',0)),
                        x.get('imp_banner_impressions_30',0),
                        h.formatMoney(x.get('imp_banner_totalCost_30',0)),
                        x.get('imp_banner_impressions_365',0),
                        h.formatMoney(x.get('imp_banner_totalCost_365',0)),
                        '%.2f c' % ((x.get('imp_banner_totalCost',0)/(x.get('imp_banner_impressions',0)/1000))*100 if x.get('imp_banner_totalCost',0)>0 and x.get('imp_banner_impressions',0)>0 else 0),
                        '%.2f c' % ((x.get('imp_banner_totalCost_2',0)/(x.get('imp_banner_impressions_2',0)/1000))*100 if x.get('imp_banner_totalCost_2',0)>0 and x.get('imp_banner_impressions_2',0)>0 else 0),
                        '%.2f c' % ((x.get('imp_banner_totalCost_7',0)/(x.get('imp_banner_impressions_7',0)/1000))*100 if x.get('imp_banner_totalCost_7',0)>0 and x.get('imp_banner_impressions_7',0)>0 else 0),
                        2 if x['activity'] == "greenflag" else 1))
                    
            totalSummToday += (x.get('imp_banner_totalCost',0))
            totalSummYesterday += (x.get('imp_banner_totalCost_2',0))
            totalSummBeforeYesterday += (x.get('imp_banner_totalCost_3',0))
            totalSummWeek += (x.get('imp_banner_totalCost_7',0))
            totalSummMonth += (x.get('imp_banner_totalCost_30',0))
            totalSummYear += (x.get('imp_banner_totalCost_365',0))
            totalImpToday += (x.get('imp_banner_impressions',0))
            totalImpYesterday += (x.get('imp_banner_impressions_2',0))
            totalImpBeforeYesterday += (x.get('imp_banner_impressions_3',0))
            totalImpWeek += (x.get('imp_banner_impressions_7',0))
            totalImpMonth += (x.get('imp_banner_impressions_30',0))
            totalImpYear += (x.get('imp_banner_impressions_365',0))

            
        userdata = {'user': u'ИТОГО:',
                    'impToday': totalImpToday,
                    'summToday': h.formatMoney(totalSummToday),
                    'impYesterday': totalImpYesterday,
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'impBeforeYesterday': totalImpBeforeYesterday,
                    'summBeforeYesterday': h.formatMoney(totalSummBeforeYesterday),
                    'impWeek': totalImpWeek,
                    'summWeek': h.formatMoney(totalSummWeek),
                    'impMonth': totalImpMonth,
                    'summMonth': h.formatMoney(totalSummMonth),
                    'impYear': totalImpYear,
                    'summYear': h.formatMoney(totalSummYear)
                   }
        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
            if iCol in [3,5,7,9,11,13,14,15,16]:
                data.sort(key=lambda x: float(str(x[iCol-1].partition(' ')[0])), reverse = r)
            else:
                data.sort(key=lambda x: x[iCol-1], reverse = r)        
        return h.jgridDataWrapper(data, userdata)

    def dataBannerUsersClick(self):
        """Суммарные данные по всем пользователям"""
        users = self._usersList()
        data = []
        totalSummToday = 0
        totalSummYesterday = 0
        totalSummBeforeYesterday = 0
        totalSummWeek = 0
        totalSummMonth = 0
        totalSummYear = 0
        totalImpToday = 0
        totalImpYesterday = 0
        totalImpBeforeYesterday = 0
        totalImpWeek = 0
        totalImpMonth = 0
        totalImpYear = 0
        for x in app_globals.db.stats_user_summary.find().sort('registrationDate'):
            if x['user'] not in users: continue
            link_class = "actionLink %s" % x['activity']
            if self._is_yellow_star(x):
                link_class += " yellow_star"
            banner_click_cost_avg = x.get('banner_totalCost',0) / x.get('banner_clicksUnique',0) if (x.get('banner_totalCost',0) > 0 and x.get('banner_clicksUnique',0) > 0) else 0
            banner_click_cost_avg2 = x.get('banner_totalCost_2',0) / x.get('banner_clicksUnique_2',0) if (x.get('banner_totalCost_2',0) > 0 and x.get('banner_clicksUnique_2',0) > 0) else 0
            banner_click_cost_avg7 = x.get('banner_totalCost_7',0) / x.get('banner_clicksUnique_7',0) if (x.get('banner_totalCost_7',0) > 0 and x.get('banner_clicksUnique_7',0) > 0) else 0
            ctr = 100.0 *  x.get('banner_clicksUnique',0) / x.get('banner_impressions',0) if (x.get('banner_clicksUnique',0) > 0 and x.get('banner_impressions',0) > 0) else 0
            ctr2 = 100.0 *  x.get('banner_clicksUnique_2',0) / x.get('banner_impressions_2',0) if (x.get('banner_clicksUnique_2',0) > 0 and x.get('banner_impressions_2',0) > 0) else 0
            ctr7 = 100.0 *  x.get('banner_clicksUnique_7',0) / x.get('banner_impressions_7',0) if (x.get('banner_clicksUnique_7',0) > 0 and x.get('banner_impressions_7',0) > 0) else 0
            data.append(('<a href="javascript:;" class="%s" >%s</a>' % (link_class, x['user']),
                        h.formatMoney(x.get('banner_totalCost',0)),
                        x.get('banner_impressions',0),
                        '%.3f' % ctr,
                        '%.2f c' % (banner_click_cost_avg * 100),
                        h.formatMoney(x.get('banner_totalCost_2',0)),
                        x.get('banner_impressions_2',0),
                        '%.3f' % ctr2,
                        '%.2f c' % (banner_click_cost_avg2 * 100),
                        h.formatMoney(x.get('banner_totalCost_3',0)),
                        h.formatMoney(x.get('banner_totalCost_7',0)),
                        x.get('banner_impressions_7',0),
                        '%.3f' % ctr7,
                        '%.2f c' % (banner_click_cost_avg7 * 100),
                        h.formatMoney(x.get('banner_totalCost_30',0)),
                        h.formatMoney(x.get('banner_totalCost_365',0)),
                        2 if x['activity'] == "greenflag" else 1))
                        
            totalSummToday += (x.get('banner_totalCost',0))
            totalSummYesterday += (x.get('banner_totalCost_2',0))
            totalSummBeforeYesterday += (x.get('banner_totalCost_3',0))
            totalSummWeek += (x.get('banner_totalCost_7',0))
            totalSummMonth += (x.get('banner_totalCost_30',0))
            totalSummYear += (x.get('banner_totalCost_365',0))
            totalImpToday += (x.get('banner_impressions',0))
            totalImpYesterday += (x.get('banner_impressions_2',0))
            totalImpWeek += (x.get('banner_impressions_7',0))

            
        userdata = {'user': u'ИТОГО:',
                    'impToday': totalImpToday,
                    'summToday': h.formatMoney(totalSummToday),
                    'impYesterday': totalImpYesterday,
                    'summYesterday': h.formatMoney(totalSummYesterday),
                    'summBeforeYesterday': h.formatMoney(totalSummBeforeYesterday),
                    'impWeek': totalImpWeek,
                    'summWeek': h.formatMoney(totalSummWeek),
                    'summMonth': h.formatMoney(totalSummMonth),
                    'summYear': h.formatMoney(totalSummYear)
                   }
        if 'sortcol' in request.params:
            iCol = int(request.params.get('sortcol', 0)) 
            r = (request.params.get('sortreverse') == "desc")
            if iCol in [2,4,5,6,8,9,10,11,13,14,15,16]:
                data.sort(key=lambda x: float(str(x[iCol-1].partition(' ')[0])), reverse = r)
            else:
                data.sort(key=lambda x: x[iCol-1], reverse = r)        
        return h.jgridDataWrapper(data, userdata)


    def account_current_CTR(self, user_login):
        ''' Текущий CTR аккаунта ``user_login`` '''
        ads = [x['guid'] for x in app_globals.db.informer.find({'user': user_login})]
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)
        start_date = today - timedelta(days=7) 
        date_cond = {'$gte': start_date, '$lte': today}   
                                           
        clicks_imp = app_globals.db.stats_daily_adv.group([],
                                     {'adv': {'$in': ads},
                                      'date': date_cond},
                                     {'clicksUnique': 0, 'impressions': 0},
                                     'function(o,p) {p.clicksUnique += o.clicksUnique; p.impressions += o.impressions;}')
        try:
            ctr = float(100 * clicks_imp[0].get('clicksUnique')) / float(clicks_imp[0].get('impressions'))
        except:
            ctr = 0
        return ctr

    def accountTodaySumm(self, user_login):
        """ заработано партнером за сегодня """
        from datetime import date
        d = date.today()
        today = datetime(d.year, d.month, d.day)
        dateCond = today
        return model.accountPeriodSumm(dateCond, user_login)
        
    def accountYesterdaySumm(self, user_login):
        """  заработано партнером за вчера """
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)   
        one_day = timedelta(days=1)
        yesterday = today - one_day
        dateCond = yesterday
        return model.accountPeriodSumm(dateCond, user_login)
    
    def accountBeforeYesterdaySumm(self, user_login):
        """  заработано партнером за позавчера """
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)   
        two_day = timedelta(days=2)
        yesterday = today - two_day
        dateCond = yesterday
        return model.accountPeriodSumm(dateCond, user_login)
    
    def accountWeekSumm(self, user_login):
        """ заработано партнером за неделю"""
        d = datetime.today()
        today = datetime(d.year, d.month, d.day)
        one_week = timedelta(weeks=1)
        weekstart = today - one_week
        dateCond = {'$gte': weekstart, '$lte': today} 
        return model.accountPeriodSumm(dateCond, user_login)
    

    def domainsRequests(self):
        ''' Возвращает список заявок на регистрацию домена '''
        if not c.user: return h.userNotAuthorizedError()
        if not Permission(Account(c.user)).has(Permission.USER_DOMAINS_MODERATION): return h.jgridDataWrapper([])
        result = []
        for user_item in app_globals.db.domain.find({'requests': {'$exists': True}}):
            for request in user_item['requests']:
                row = (user_item['login'], '', request, '')
                result.append(row)
        return h.jgridDataWrapper(result)
        
    
    @current_user_check 
    @expandtoken    
    @authcheck     
    def approveDomain(self):
        ''' Одобряет заявку на регистрацию домена '''
        if not Permission(Account(c.user)).has(Permission.VIEW_MONEY_OUT): return h.insufficientRightsError() 
        try:
            user = request.params['user'] 
            domain = request.params['domain']
            account = Account(login=user)
            account.domains.approve_request(domain)
            return h.JSON({'error': False})
        except KeyError:
            return h.JSON({'error': True, 'message': 'params error'})
        except:
            return h.JSON({'error': True})
        
    @current_user_check 
    @expandtoken    
    @authcheck     
    def rejectDomain(self):
        ''' Отклоняет заявку на регистрацию домена '''
        if not Permission(Account(c.user)).has(Permission.VIEW_MONEY_OUT): return h.insufficientRightsError() 
        try:
            user = request.params['user'] 
            domain = request.params['domain']
            account = Account(login=user)
            account.domains.reject_request(domain)
            return h.JSON({'error': False})
        except KeyError:
            return h.JSON({'error': True, 'message': 'params error'})
        except:
            return h.JSON({'error': True})
            
        
    def _usersList(self):
        """ Возвращает список пользователей """
        if not c.user: return []
        users_condition = {'manager': {'$ne' : True}}
        if not Permission(Account(login=c.user)).has(Permission.VIEW_ALL_USERS_STATS):
            users_condition.update({'managerGet': c.user})
        users = [x['login'] for x in app_globals.db.users.find(users_condition).sort('registrationDate')]
        return users
    
    
    @current_user_check
    def userDetails(self):
        """ Вкладка детальной информации о пользователе """
        c.permission = Permission(Account(login=c.user))
        c.login = request.params.get('login')
        c.token = request.params.get('token')
        c.div_to_open = h.JSON(request.params.get('div'))
        if not c.login:
            return h.JSON({"error": True, 'msg': u'Неверно указаны параметры',
                           'ok': False})
        edit_account = model.Account(c.login)
        edit_account.load()
        c.edit_min_out_sum = edit_account.min_out_sum
        c.click_percent = edit_account.click_percent
        c.click_cost_min = edit_account.click_cost_min
        c.click_cost_max = edit_account.click_cost_max
        c.imp_percent = edit_account.imp_percent
        c.imp_cost_min = edit_account.imp_cost_min
        c.imp_cost_max = edit_account.imp_cost_max
        c.edit_manager_get = edit_account.manager_get
        c.list_manager = model.active_managers()
        c.edit_name = edit_account.owner_name
        c.edit_phone = edit_account.phone
        c.edit_email = edit_account.email
        c.edit_money_web_z = 'webmoney_z' in edit_account.money_out_paymentType
        c.edit_money_card = 'card' in edit_account.money_out_paymentType
        c.edit_money_factura = 'factura' in edit_account.money_out_paymentType
        c.edit_money_yandex = 'yandex' in edit_account.money_out_paymentType
        c.edit_account_error_messages = ''
        c.edit_prepayment = edit_account.prepayment
        c.edit_account_blocked = edit_account.blocked or ''
        c.account_domains = edit_account.domains.list()
        c.domains_categories = {}
        for x in c.account_domains:
            categories = [y['categories'] for y in app_globals.db.domain.categories.find({'domain': x}) or []]
            if len(categories) > 0:
                c.domains_categories[x] = categories[0]
            else:
                c.domains_categories[x] = []
        c.categories = [{'title': x['title'], 'guid': x['guid']} for x in app_globals.db.advertise.category.find()]
        informersData = []
        for item in edit_account.informers():
            guid = item.guid
            title = item.domain + ' ' + item.title
            if item.cost:
                click_percent = int(item.cost.get('ALL',{}).get('click',{}).get('percent',50))
                click_cost_min = float(item.cost.get('ALL',{}).get('click',{}).get('cost_min',  0.01))
                click_cost_max = float(item.cost.get('ALL',{}).get('click',{}).get('cost_max', 1.00))
                imp_percent = int(item.cost.get('ALL',{}).get('imp',{}).get('percent',50))
                imp_cost_min = float(item.cost.get('ALL',{}).get('imp',{}).get('cost_min',  0.05))
                imp_cost_max = float(item.cost.get('ALL',{}).get('imp',{}).get('cost_max', 2.00))
            else:
                click_percent = c.click_percent
                click_cost_min = c.click_cost_min
                click_cost_max = c.click_cost_max
                imp_percent = c.imp_percent
                imp_cost_min = c.imp_cost_min
                imp_cost_max = c.imp_cost_max
            informersData.append((guid,
                                  title,
                                  click_percent,
                                  click_cost_min,
                                  click_cost_max,
                                  imp_percent,
                                  imp_cost_min,
                                  imp_cost_max
                                  ))
        c.informers = h.jqGridLocalData(informersData, ['id', 'title', 'click_percent', 'click_cost_min', 'click_cost_max', 'imp_percent', 'imp_cost_min', 'imp_cost_max'])
        c.accountMoneyOutHistory = self.accountMoneyOutHistory(c.login)
        c.accountSumm = edit_account.report.balance()
        c.prepayment = edit_account.prepayment

        return render("administrator/user-details.mako.html")
    def informer_cost_save(self):
        informer = model.Informer()
        guid = request.params.get('id','')
        informer.loadGuid(guid)
        click_percent = int(request.params.get('click_percent',50))
        click_cost_min = float(request.params.get('click_cost_min',0.02))
        click_cost_max = float(request.params.get('click_cost_max',0.2))
        imp_percent = int(request.params.get('imp_percent',50))
        imp_cost_min = float(request.params.get('imp_cost_min',0.05))
        imp_cost_max = float(request.params.get('imp_cost_max',2))
        informer.cost = {u'ALL': {u'imp': {u'percent': imp_percent, u'cost_min': imp_cost_min, u'cost_max': imp_cost_max},\
                        u'click': {u'percent': click_percent, u'cost_min': click_cost_min, u'cost_max': click_cost_max}}}
        informer.save()


    def userDomainDetails(self):
        ''' Таблица статистики по доменам пользователя.
        
            Логин пользователя передаётся в GET-параметре ``user``.
        '''
        #TODO довести до ума db.stats_daily_domain и выберать данные с неё!
        user = request.params.get('user')
        db = app_globals.db
        date_start = h.trim_time(datetime.today() - timedelta(days=300))
        data_by_date_and_domain = {}
        for x in db.stats_daily_adv.find({'user': user,
                                          'date': {'$gte': date_start}}):
            key = (x['date'], x['domain'])
            record = data_by_date_and_domain \
                         .setdefault(key, {'clicks': 0,
                                           'unique': 0,
                                           'imp': 0,
                                           'imp_ban': 0,
                                           'imp_block':0,
                                           'tsumm':0,
                                           'bsumm':0,
                                           'summ': 0,
                                           'soc_clicks': 0,
                                           'soc_imp': 0,
                                           'soc_imp_block':0})
            record['clicks'] += x.get('clicks', 0)
            record['unique'] += x.get('clicksUnique', 0)
            record['imp'] += x.get('impressions', 0)
            record['imp_ban'] += x.get('banner_impressions', 0) if not x.get('isOnClick',True) else 0
            record['imp_block'] += x.get('impressions_block', 0)
            record['tsumm'] += x.get('teaser_totalCost',0) if x.get('isOnClick',True) else 0
            record['bsumm'] += x.get('totalCost',0) if not x.get('isOnClick',True) else 0
            record['summ'] += x.get('totalCost', 0)
            record['soc_clicks'] += x.get('social_clicks', 0)
            record['soc_imp'] += x.get('social_impressions', 0)
            record['soc_imp_block'] += x.get('social_impressions_block', 0)


        # Сортировка
        raw_data = data_by_date_and_domain.items()
        reverse = request.params.get('sord') == 'desc'
        sidx = request.params.get('sidx')
        if not sidx:
            # Параметры по умолчанию
            sidx = 'date'
            reverse = True

        if sidx == 'date':
            # сначала по дате, затем по домену
            sfunc = lambda x: '%s %s' % (x[0][0].strftime('%Y%m%d'), x[0][1])
        else:
            # сначала по домену, затем по дате
            sfunc = lambda x: '%s %s' % (x[0][1], x[0][0].strftime('%Y%m%d'))

        raw_data.sort(key=sfunc, reverse=reverse)
 
        # Форматируем вывод в таблицу
        data = []
        for k, v in raw_data:
            date, domain = k
            if v['imp']:
                ctr = v['unique'] * 100.0 / v['imp']
            else:
                ctr = 0
            if v['imp_block']:
                ctr_block = v['unique'] * 100.0 / v['imp_block']
            else:
                ctr_block = 0
            data.append((date.strftime("%d.%m.%Y"),
                         domain,
                         v['clicks'],
                         v['unique'],
                         v['imp'],
                         '%.2f c' % ((float(v['tsumm']) / v['unique']) *100 if (v['tsumm'] > 0) and (v['unique'] >0) else 0),
                         v['imp_ban'],
                         '%.2f c' % ((float(v['bsumm']) / (v['imp_ban']/1000.0)) *100 if (v['bsumm'] > 0) and (v['imp_ban'] >0) else 0),
                         v['imp_block'],
                         '%.3f' % ctr,
                         '%.3f' % ctr_block,
                         '%.2f' % v['tsumm'],
                         '%.2f' % v['bsumm'],
                         '%.2f' % v['summ'],
                         v['soc_clicks'],
                         v['soc_imp'],
                         v['soc_imp_block']
                         ))

        return h.jgridDataWrapper(data)
        



    
    @current_user_check
    @expandtoken    
    @authcheck 
    def setNewPassword(self):
        ''' Устанавливает новый пароль для пользователя''' 
        try:
            password = request.params['psw']
            login = request.params['login']
            app_globals.db.users.update({'login': login}, {'$set': {'password': password}})
            return h.JSON({'error': False})
        except:    
            return h.JSON({'error': True})
        
    def generateNewPassword(self):
        ''' Генерирует пароль'''
        try:
            new_password = model.makePassword()
            return h.JSON({'error': False, 'new_password': new_password})
        except:
            return h.JSON({'error': True})
    
    class PaymentTypeNotDefined(Exception):
        ''' Не выбран ни один способ вывода средств '''
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return 'PaymentTypeNotDefined'
        
        
        
    @current_user_check 
    @expandtoken    
    @authcheck
    def checkCurrentUser(self):
        ''' Функция для проверки аутентичности пользователя и токена, 
        возвращает только статус проверки и ничего не делает'''
        return h.JSON({"error": False})        
        

    @current_user_check 
    @expandtoken    
    @authcheck
    def saveUserDetails(self):
        """ Сохранение информации о пользователе """
        c.login = request.params.get('login')
        edit_account = model.Account(c.login)
        edit_account.load()
        schema = updateUserForm()
        try: 
            form_result = schema.to_python(dict(request.params))
            c.edit_money_card = False if not request.params.get('edit_money_card') else True
            c.edit_money_web_z = False if not request.params.get('edit_money_web_z') else True
            c.edit_money_factura = False if not request.params.get('edit_money_factura') else True
            if (not c.edit_money_card and not c.edit_money_web_z and not c.edit_money_factura):
                    raise ManagerController.PaymentTypeNotDefined('Payment_type_not_defined')
        except formencode.Invalid, error:
            return h.JSON({'error': True, 'msg': '\n'.join([x.msg for x in error.error_dict.values()])})
        except self.PaymentTypeNotDefined:
            return h.JSON({'error': True, 'msg': u'Укажите хотя бы один способ вывода средств!'})
                      
        edit_account.min_out_sum = request.params.get('edit_minsum')
        edit_account.click_percent = request.params.get('click_percent')
        edit_account.click_cost_min = request.params.get('click_cost_min')
        edit_account.click_cost_max = request.params.get('click_cost_max')
        edit_account.imp_percent = request.params.get('imp_percent')
        edit_account.imp_cost_min = request.params.get('imp_cost_min')
        edit_account.imp_cost_max = request.params.get('imp_cost_max')
        edit_account.owner_name = request.params.get('edit_name')
        edit_account.manager_get = request.params.get('edit_manager_get')
        edit_account.phone = request.params.get('edit_phone')
        edit_account.email = request.params.get('edit_email')
        edit_account.money_card = False if not request.params.get('edit_money_card') else True
        edit_account.money_web_z = False if not request.params.get('edit_money_web_z') else True
        edit_account.money_factura = False if not request.params.get('edit_money_factura') else True
        edit_account.money_yandex = False if not request.params.get('edit_money_yandex') else True
        edit_account.prepayment = False if not request.params.get('edit_prepayment') else True
        edit_account.blocked = request.params.get('edit_account_blocked', False)
        edit_account.update()
        return h.JSON({'error': False})
    
    @current_user_check
    @expandtoken    
    @authcheck 
    def saveDomainCategories(self):
        '''Сохранение настроек категорий для домена аккаунта'''
        try:
            categories = request.params.getall('categories')
            domain = request.params.get('account_domains')
            if len(domain) == 0:
                return h.JSON({'error': True, 'msg': u'Ошибка! Не указан домен!'})
            app_globals.db.domain.categories.update({'domain': domain},
                                                    {'$set':
                                                           {'categories': categories} 
                                                     },
                                                     upsert=True)
            login = request.params.get('login')
            edit_account = model.Account(login)
            edit_account.load()
            account_domains = edit_account.domains.list()
            domains_categories = {}
            for x in account_domains:
                categories = [y['categories'] for y in app_globals.db.domain.categories.find({'domain': x})]
                if len(categories) > 0:
                    domains_categories[x] = categories[0]
                else:     
                    domains_categories[x] = []
            try:
                mq.MQ().account_update(login)
            except:
                return h.JSON({'error': True,
                               'msg': u'Сохранения изменены, но из-за ошибки AMQP временно не будут применяться. Свяжитесь с администратором. '})
        except:
            return h.JSON({'error': True})
            
        return h.JSON({'error': False, 'domains_categories': domains_categories})

    @current_user_check 
    @expandtoken    
    @authcheck 
    def moneyOutSubmit(self):
        ''' Заявка от менеджера на вывод его средств'''
        schema = MoneyOutForm()
        try:
            form = schema.to_python(dict(request.params))
        except formencode.Invalid, error:
            errorMessage = '<br/>\n'.join([x.msg for x in error.error_dict.values()])
            return json.dumps({'error': True, 'msg': errorMessage, 'ok': False}, ensure_ascii=False)
        
        app_globals.db.money_out_request.insert(
                        {
                             'date': datetime.now(),
                             'user': {'guid': '',
                                      'login': c.manager_login},
                             'summ': form.get('moneyOut_summ'),
                             'comment': form.get('moneyOut_comment')
                        })
        return json.dumps({'error': False, 'ok': True, 'msg': 'Заявка успешно принята'})
    
    def moneyOutHistory(self):
        """История вывода денег"""
        user = request.environ.get('CURRENT_USER')
        if not user: return h.userNotAuthorizedError()

        data = AccountReports(Account(user)).money_out_requests()
        data.sort(key=lambda x:x['date'])
        
        table = [(x['date'].strftime("%d.%m.%Y"),
                  '%.2f $' % x['summ'],
                  x.get('comment') if x.get('approved') else u'заявка обрабатывается...')
                 for x in data]
        return h.jgridDataWrapper(table)
    
    def accountMoneyOutHistory(self, account_login):
        ''' История вывода средств пользователя account_login''' 
        data = AccountReports(Account(account_login)).money_out_requests()
        data.sort(key=lambda x:x['date'], reverse=True)
        return self.tableForDataMoneyOutRequest(data)
    
    @current_user_check 
    @expandtoken    
    @authcheck
    def moneyOutRemove(self):
        ''' Убирает заявку менеджера на вывод его средств'''
        try:
            id = int(request.params['id'])
            obj = app_globals.db.money_out_request.find({'user.login': c.manager_login}).sort('date')[id-1]

            if obj.get('approved', False):
                return h.JSON({'error': True, 'msg': u'Эта заявка уже была выполнена'})
            app_globals.db.money_out_request.remove(obj, safe=True)
        except:
            return h.JSON({'error': True, 'ok': False})

        return h.JSON({'error': False, 'ok': True, 'msg': 'Заявка успешно отменена'})    


    def openSchetFacturaFile(self):
        ''' Открывает файл счёт фактуры'''
        try:
            filename = request.params.get('filename')
            file = open('%s/%s' % (config.get('schet_factura_folder'), filename), 'rb')
        except:
            return u'Файл не найден!'
        
        content_type = {'.doc': 'application/msword',
                        '.docx': 'application/msword',
                        '.odt': 'application/msword',
                        '.rtf': 'application/msword',
                        '.pdf': 'application/pdf',
                        '.zip': 'application/zip',
                        '.odt': 'application/vnd.oasis.opendocument.text'}
        extension = os.path.splitext(filename)[1].lower()
        response.headers['Content-type'] = \
            content_type.get(extension, 'application/octet-stream')  
        return file
    
    def checkInformers(self, country):
        ''' Страница проверки работоспособности информеров в стране ``country`` '''
        user = request.environ.get('CURRENT_USER') or session.get('adload_user')
        if not user:
            return h.userNotAuthorizedError()

        region = request.params.get('region', '')

        def get_int(str):
            try:
                return int(re.findall("[0-9]+", str)[0])
            except:
                return 0
        
        c.informers = []
        for inf in app_globals.db.informer\
                           .find({}, ['guid', 'title', 'user', 'domain', 'admaker'])\
                           .sort('user'):
            try:
                width = get_int(inf['admaker']['Main']['width']) + 2 * get_int(inf['admaker']['Main']['borderWidth'])
                height = get_int(inf['admaker']['Main']['height']) + 2 * get_int(inf['admaker']['Main']['borderWidth'])
                valid = True
            except:
                width = height = 0
                valid = False
            c.informers.append({'guid': inf['guid'],
                                'title': inf['title'],
                                'user': str(inf['user']),
                                'domain': inf.get('domain'),
                                'width': width,
                                'height': height,
                                'valid': valid})
        c.country = country
        c.all_geo_regions = [(x['region'], x.get('ru')) for x in app_globals.db.geo.regions.find({'country': c.country}).sort('ru')]
        c.all_geo_regions.insert(0, ('', u'(любая область)'))
        c.selected_region = region
        try:
            c.getmyad_worker_server = config['getmyad_worker_server']
        except KeyError:
            return 'В конфигурации не указан адрес сервера показа рекламы (см. ключ getmyad_worker_server)'
            
        return render('/informers.check.mako.html')

    @current_user_check 
    @expandtoken    
    @authcheck 
    def updateProtection(self):
        if not Permission(Account(login=c.user)).has(Permission.VIEW_MONEY_OUT):
            return h.insufficientRightsError()

        user = request.params.get('user', None)
        date = h.datetimeFromStr(request.params.get('date'))

        if not user or not date:
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        protectionCode = request.params.get('protectionCode', '')
        protectionPeriod = request.params.get('protectionPeriod', '')

        if len(protectionCode) and not protectionCode.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        if len(protectionPeriod) and not protectionPeriod.isdigit():
            return json.dumps({'error': True, 'msg': 'invalid arguments', 'ok': False})

        db = app_globals.db

        money_out_request = \
            db.money_out_request.find_one({'user.login': user,
                                           'date': {'$gte': date,
                                                    '$lte': (date + timedelta(seconds=60))}})

        money_out_request['protectionCode'] = protectionCode
        money_out_request['protectionDate'] = datetime.now() + timedelta(days=int(protectionPeriod)) if len(protectionPeriod) else ''
        db.money_out_request.save(money_out_request, safe=True)
        
        return h.JSON({'error': False, 'ok': True,
                       'date': date.strftime("%d.%m.%Y %H:%M"),
                       'date2': (date + timedelta(seconds=60))\
                                        .strftime("%d.%m.%Y %H:%M")})



class MoneyOutForm(formencode.Schema):
    """Форма вывода денег на web money"""
    allow_extra_fields = True
    filter_extra_fields = True
    moneyOut_summ = v.Number(min=10,
                             not_empty=True,
                             messages={'empty': u'Пожалуйста, введите сумму!',
                                       'number': u'Пожалуйста, введите корректную сумму!',
                                       'tooLow': u'Сумма должна быть не менее %(min)s $!'})
    moneyOut_comment = v.String(if_missing=None)
        
    
class updateUserForm(Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        
        edit_name = formencode.validators.String(not_empty=True, messages={'empty':u'Введите ФИО!'})
        edit_phone = formencode.validators.String(not_empty=True, messages={'empty':u'Введите телефон!'})
        edit_email = formencode.validators.Email(not_empty=True, messages={'empty':u'Введите e-mail!',
                                                                      'noAt': u'Неправильный формат e-mail!',
                                                                      'badUsername': u'Неправильный формат e-mail!',
                                                                      'badDomain': u'Неправильный формат e-mail!'})
