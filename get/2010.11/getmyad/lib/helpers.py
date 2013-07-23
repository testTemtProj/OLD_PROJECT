# This Python file uses the following encoding: utf-8
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

from routes import url_for
from webhelpers.html.tags import *
from datetime import datetime
from pylons.controllers.util import redirect
import json
import pymongo.json_util


class progressBar:
    def __init__(self, minValue = 0, maxValue = 10, totalWidth=12):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = minValue
        self.max = maxValue
        self.span = maxValue - minValue
        self.width = totalWidth
        self.amount = 0       # When amount == max, we are 100% done 
        self.updateAmount(0)  # Build progress bar string

    def updateAmount(self, newAmount = 0):
        if newAmount < self.min: newAmount = self.min
        if newAmount > self.max: newAmount = self.max
        self.amount = newAmount

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.amount - self.min)
        percentDone = (diffFromMin / float(self.span)) * 100.0
        percentDone = round(percentDone)
        percentDone = int(percentDone)

        # Figure out how many hash bars the percentage should be
        allFull = self.width - 2
        numHashes = (percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # build a progress bar with hashes and spaces
        self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

        # figure out where to put the percentage, roughly centered
        percentPlace = (len(self.progBar) / 2) - len(str(percentDone)) 
        percentString = str(percentDone) + "%"

        # slice the percentage into the bar
        self.progBar = self.progBar[0:percentPlace] + percentString + self.progBar[percentPlace+len(percentString):]

    def __str__(self):
        return str(self.progBar)



def dateFromStr(str):
    """Возвращает объект datetime из строки вида 'чч.мм.гггг' """
    try:
        day = int(str[0:2])
        month = int(str[3:5])
        year = int(str[6:10])
        return datetime(year, month, day)
    except:
        return None


def datetimeFromStr(str):
    """Возвращает объект datetime из строки вида 'чч.мм.гггг ЧЧ:ММ' """
    try:
        day = int(str[0:2])
        month = int(str[3:5])
        year = int(str[6:10])
        hour = int(str[11:13])
        minute = int(str[14:16])
        return datetime(year, month, day, hour, minute)
    except:
        return None


def userNotAuthorizedError():
    return JSON({'error': True, 'error_type': 'authorizedError', 'msg': u"Пожалуйста, войдите в систему GetMyAd", 'ok': False}) 

def insufficientRightsError():
    return JSON({'error': True, 'msg': u"Недостаточно прав для осуществления операции", 'ok': False}) 


def jgridDataWrapper(data, userdata = None):
    """Принимает список значений колонок и возвращает json для таблиц jqGrid """
    output = {'total': 1,
               'page': 1,
               'records': len(data),
               'rows': [{'cell': x, 'id': index + 1} for index,x in enumerate(data)]
               }
    if userdata:
        output['userdata'] = userdata
    return JSON(output)


def formatMoney(value):
    """ Форматирует денежную величину """
    return '%.2f $' % value


def JSON(obj):
    """Возвращает JSON-представление объекта obj"""
    return json.dumps(obj, default=pymongo.json_util.default, ensure_ascii=False)


def cursor_to_list(cursor):
    """ Преобразует курсор MongoDB в список объектов """
    return [x for x in cursor]
