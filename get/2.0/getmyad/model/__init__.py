# This Python file uses the following encoding: utf-8
from datetime import datetime, timedelta
from ftplib import FTP
from getmyad.config.social_ads import social_ads
from getmyad.lib.helpers import progressBar
from getmyad.lib.app_globals import Globals
from pylons import app_globals, config
from pymongo import ASCENDING, DESCENDING
from uuid import uuid1
import StringIO
import getmyad
import getmyad.lib.helpers as h
import logging
import mq
import pymongo
import re

from MoneyOutRequest import  MoneyOutRequest, WebmoneyMoneyOutRequest, CardMoneyOutRequest,YandexMoneyOutRequest, InvoiceMoneyOutRequest
from Account import Account, AccountReports, ManagerReports, Permission
from Informer import Informer, InformerFtpUploader
from StatisticReports import StatisticReport


try:
    db = app_globals.create_mongo_connection()
except:
    db = None


def makePassword():
    """Возвращает сгенерированный пароль"""
    from random import Random
    rng = Random()

    righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
    lefthand = '789yuiophjknmYUIPHJKLNM'
    allchars = righthand + lefthand
    
    passwordLength = 8
    alternate_hands = True
    password = ''
    
    for i in range(passwordLength):
        if not alternate_hands:
            password += rng.choice(allchars)
        else:
            if i % 2:
                password += rng.choice(lefthand)
            else:
                password += rng.choice(righthand)
    return password

    
def allAdvertiseScriptsSummary(user_login, dateStart = None, dateEnd = None):
    """Возвращает суммарную статистику по всем площадкам пользователя user_id"""
    global db
    ads = {}
    for t in [{x['guid'] : x.get('domain', '') + ', ' + x['title']} for x in db.informer.find({"user": user_login})]:
        ads.update(t)
    
    reduce = 'function(o,p) {' \
        '    p.clicks += o.clicks || 0;' \
        '    p.unique += o.clicksUnique || 0;' \
        '    p.impressions += o.impressions || 0;' \
        '    p.totalCost += o.totalCost || 0;' \
        '}' 
    condition = {'adv': {'$in': ads.keys()}}
    dateCondition = {}
    if dateStart <> None: dateCondition['$gte'] = dateStart
    if dateEnd <> None:   dateCondition['$lte'] = dateEnd
    if len(dateCondition) > 0:
        condition['date'] = dateCondition
    
    res = db.stats_daily_adv.group(['adv'],
                                   condition,
                                   {'clicks':0, 'unique':0, 'impressions':0, 'totalCost':0},
                                   reduce)
    for x in res:
        x['advTitle'] = ads[x['adv']]
    
    return res


def updateTime():
    """Возвращает последнее время обновления статистики"""
    value = app_globals.db.config.find_one({'key': 'last stats_daily update date'})
    if value is None:
        return None
    date = value.get('value')
    return date if isinstance(date, datetime) else None


def users():
    """Возвращает список пользователей GetMyAd"""
    return [{
             'guid': x.get('guid'),
             'login': x['login'],
             'title': x.get('title'),
             'registrationDate': x['registrationDate'],
             'manager': x.get('manager', False)
            }
             for x in app_globals.db.users.find().sort('registrationDate')]


def active_managers():
    ''' Возвращает список активных менеджеров '''
    return [x['login']
            for x in app_globals.db.users.find({
                        'manager': True,
                        'blocked': {'$ne': 'banned'}})]


def currentClickCost():
    """ Текущие расценки для каждого пользователя.

        Работает как генератор. Формат возвращаемых записей различается в
        зависимости от типа расценок.

        Для фиксированной цены за клик::

            {'date': datetime.datetime,     # Время вступления расценки в силу
             'user_login': String,          # Логин пользователя
             'type': 'fixed',               # Тип расценки
             'cost': Decimal                # Фиксированная цена за клик
            }

        Для плавающей цены::

            {'date': datetime.datetime,     # Время вступления расценки в силу
             'user_login': String,          # Логин пользователя
             'type': 'floating',            # Тип расценки
             'percent': Decimal,            # Процент от цены рекламодателя
             'min': Decimal or None,        # Нижний порог цены
             'max': Decimal or None         # Верхний порог цены
            }
    """
    for user in users():
        if user['manager']:
            continue
        cursor = db.click_cost.find({'user.login': user['login']}) \
                              .sort('date', DESCENDING) \
                              .limit(1)
        if cursor.count() == 0:
            # Цена за клик ещё не установлена
            yield { 'date': None,
                    'user_login': user['login'],
                    'type': 'fixed',
                    'cost': 0
                  }
            continue
        x = cursor[0]
        if x.get('type') == 'floating':
            # Плавающая цена за клик
            yield {'date': x['date'],
                   'user_login': x['user']['login'],
                   'type': 'floating',
                   'percent': x['percent'],
                   'min': x['min'],
                   'max': x['max']
                  }
        else:
            # Фиксированная цена за клик
            yield {'date': x['date'],
                   'user_login': x['user']['login'],
                   'type': 'fixed',
                   'cost': x['cost']
                  }


def setFixedCostForClick(user_login, cost, date):
    """ Устанавливает пользователю фиксированную цену за клик.

        Параметры:
    
        ``user_login``
            Логин пользователя.

        ``cost``
            Фиксированная цена за клик, начисляемая пользователю за переход.

        ``date``
            Время/дата, начиная с которой цена вступает в действие.
    """
    assert isinstance(date, datetime)
    db.click_cost.update({'date': date,
                          'user': {#'guid': user_guid,  # TODO: Проверить, чтоб нигде не использовалось и упрость эту структуру
                                   'login': user_login}},
                         {'$set': {'cost': cost,
                                   'type': 'fixed'}},
                         upsert=True, safe=True)


def setFloatingCostForClick(user_login, date, percent, cost_min, cost_max):
    """ Устанавливает пользователю плавающую цену за клик.

        Параметры:
    
        ``user_login``
            Логин пользователя.

        ``date``
            Время/дата, начиная с которой цена вступает в действие.

        ``percent``
            Процент от цены рекламодателя, который будет начисляться
            пользователю.

        ``cost_min``
            Минимальная цена. Независимо от процента и цены рекламодателя,
            пользователю не начислится меньше этой суммы. Если равен None,
            то параметр считается не установленным и нижнего порога у цены нет.

        ``cost_max``
            Максимальная цена. Независимо от процента и цены рекламодателя,
            пользователю не начислится больше этой суммы. Если равен None,
            то параметр считается не установленным и верхнего порога у цены нет.

        Цена применяется для всех кликов, совершённых после момента установки.
    """
    assert 0 < percent <= 100
    assert isinstance(date, datetime)
    db.click_cost.update({'date': date,
                          'user': {'login': user_login}},
                         {'$set': {'percent': percent,
                                   'min': cost_min,
                                   'max': cost_max,
                                   'type': 'floating'}},
                         upsert=True, safe=True)


def setManagerPercent(manager_login, percent):
    """ Устанавливает процент менеджера"""
    app_globals.db.users.update({'login': manager_login}, {'$set':{'percent': percent}})
    now = datetime.today()
    today = datetime(now.year, now.month, now.day, 0,0,0)
    app_globals.db.manager.percent.update({'date': today,
                                          'login': manager_login},
                                           {'$set': {'percent':percent}},
                                           upsert = True)


def accountPeriodSumm(dateCond, user_login):
    ''' Возвращает сумму аккаунта за период заданный в dateCond'''
    ads = [x['guid'] for x in db.informer.find({'user': user_login})]                                       
    income = db.stats_daily_adv.group([],
                                      {'adv': {'$in': ads}, 'date': dateCond},
                                      {'sum': 0},
                                      'function(o,p) {p.sum += isNaN(o.totalCost)? 0 : o.totalCost;}')
    try:
        income = float(income[0].get('sum', 0))
    except:
        income = 0
    return income




def moneyOutApproved(user_login):
    """Возвращает список одобренных заявок"""
    return db.money_out_request.find({'user.login': user_login,
                                      'approved': True}).sort('date', ASCENDING)
    
    





class Campaign(object):
    "Класс описывает рекламную кампанию, запущенную в GetMyAd"
    
    class NotFoundError(Exception):
        'Кампания не найдена'
        def __init__(self, id):
            self.id = id
        
    
    def __init__(self, id):
        #: ID кампании
        self.id = id.lower()
        #: Заголовок рекламной кампании
        self.title = ''
        #: Является ли кампания социальной рекламой
        self.social = False
        #: Добавлять ли к ссылкам предложений маркер yottos_partner=...
        self.yottos_partner_marker = True
        #: Время последнего обновления (см. rpc/campaign.update())
        self.last_update = None
        
    def load(self):
        'Загружает кампанию из базы данных'
        c = app_globals.db.campaign.find_one({'guid': self.id})
        if not c:
            raise Campaign.NotFoundError(self.id)
        self.id = c['guid']
        self.title = c.get('title')
        self.social = c.get('social', False)
        self.yottos_partner_marker = c.get('yottosPartnerMarker', True)
        self.last_update = c.get('lastUpdate', None)
        if c.has_key('showConditions'):
            self.keywords = c['showConditions'].get('keywords', [])
            self.minus_words = c['showConditions'].get('minus_words', [])
            self.exactly_phrases = c['showConditions'].get('exactly_phrases', [])
        else:
            self.keywords = []
            self.exactly_phrases = []
            self.minus_words = []

    
    def restore_from_archive(self):
        'Пытается восстановить кампанию из архива. Возвращает true в случае успеха'
        c = app_globals.db.campaign.archive.find_one({'guid': self.id})
        if not c:
            return False
        self.delete()
        app_globals.db.campaign.save(c)
        app_globals.db.campaign.archive.remove({'guid': self.id}, safe=True)
    
    def save(self):
        'Сохраняет кампанию в базу данных'
        app_globals.db.campaign.update(
            {'guid': self.id},
            {'$set': {'title': self.title,
                      'social': self.social,
                      'yottosPartnerMarker': self.yottos_partner_marker,
                      'lastUpdate': self.last_update}},
            upsert=True, safe=True)
    
    def exists(self):
        'Возвращает ``True``, если кампания с заданным ``id`` существует'
        return (app_globals.db.campaign.find_one({'guid': self.id}) <> None)

    def delete(self):
        'Удаляет кампанию'
        app_globals.db.campaign.remove({'guid': self.id}, safe=True)
    
    def move_to_archive(self):
        'Перемещает кампанию в архив'
        c = app_globals.db.campaign.find_one({'guid': self.id})
        if not c: return
        app_globals.db.campaign.archive.remove({'guid': self.id})
        app_globals.db.campaign.archive.save(c, safe=True)
        self.delete()


class Offer(object):
    'Класс описывает рекламное предложение'
    
    def __init__(self, id):
        self.id = id.lower()
        self.title = ''
        self.price = ''
        self.url = ''
        self.image = ''
        self.description = ''
        self.date_added = None
        self.campaign = ''
        self.uniqueHits = ''
        self.keywords = []
        self.exactly_phrases = []
        self.minus_words = []
        self.listAds = []
        self.type = ''
        self.width = ''
        self.height = ''
        self.rating = ''
    
    def save(self):
        'Сохраняет предложение в базу данных'
        app_globals.db.offer.update({'guid': self.id},
                                    {'$set': {'title': self._trim_by_words(self.title, 35),
                                              'price': self.price,
                                              'url': self.url,
                                              'image': self.image,
                                              'description': self._trim_by_words(self.description, 70),
                                              'dateAdded': self.date_added,
                                              'campaignId': self.campaign,
                                              'uniqueHits': self.uniqueHits,
                                              'keywords': self.keywords,
                                              'exactly_phrases': self.exactly_phrases,
                                              'minus_words': self.minus_words,
                                              'listAds': self.listAds,
                                              'type': self.type,
                                              'width': self.width,
                                              'height': self.height,
                                              'rating': self.rating
                                              }},
                                    upsert=True, safe=True)

    def _trim_by_words(self, str, max_len):
        ''' Обрезает строку ``str`` до длины не более ``max_len`` с учётом слов '''
        if len(str) <= max_len:
            return str
        trimmed_simple = str[:max_len]
        trimmed_by_words = trimmed_simple.rpartition(' ')[0]
        return u'%s…' % (trimmed_by_words or trimmed_simple)
