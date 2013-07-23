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

log = logging.getLogger(__name__)


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
    
    
