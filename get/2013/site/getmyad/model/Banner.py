# This Python file uses the following encoding: utf-8
import pymongo
from pylons import app_globals, config
import datetime
import hashlib as h


class Banner(object):
    'Класс описывает рекламное предложение'
    
    def __init__(self, id):
        self.db = app_globals.db 
        self.id = id.lower()
        self.title = ''
        self.imp_cost = 0
        self.budget = 0
        self.url = ''
        self.image = None
        self.swf = None
        self.date_added = None
        self.campaign = ''
        self.isOnClick = False
        self.type = 'banner'
        self.width = ''
        self.height = ''

    
    def save(self):
        'Сохраняет предложение в базу данных'
        self.db.banner.offer.update({'guid': self.id},
                                    {'$set': {'title': self._trim_by_words(self.title, 35),
                                              'imp_cost': float(self.imp_cost),
                                              'budget': float(self.budget),
                                              'url': self.url,
                                              'image': self.image,
                                              'swf': self.swf,
                                              'dateAdded': self.date_added,
                                              'campaignId': self.campaign,
                                              'isOnClick': self.isOnClick,
                                              'type': self.type,
                                              'width': self.width,
                                              'height': self.height
                                              }},
                                    upsert=True, safe=True)
        if float(self.budget) > 0.0:
            date = datetime.datetime.now()
            print "Payment", float(self.budget), date
            self.db.banner.payment.insert({'guid': self.id,'budget': float(self.budget), 'date':date})

    def update(self):
        'Обнавляет предложение в базу данных'
        self.db.banner.offer.update({'guid': self.id},
                                    {'$set': {'title': self._trim_by_words(self.title, 35),
                                     'imp_cost': float(self.imp_cost),
                                     'url': self.url,
                                     'campaignId': self.campaign
                                    }},
                                    False)
        if float(self.budget) > 0.0:
            date = datetime.datetime.now()
            print "Payment", float(self.budget), date
            self.db.banner.offer.update({'guid': self.id},
                                        {'$inc': {
                                         'budget': float(self.budget)
                                        }},
                                        False)
            self.db.banner.payment.insert({'guid': self.id,'budget': float(self.budget), 'date':date})

    def load(self):
        'Загружает баннер'
        item = self.db.banner.offer.find_one({'guid': self.id})
        self.title = item.get('title')
        self.imp_cost = item.get('imp_cost')
        self.budget = item.get('budget')
        self.url = item.get('url')
        self.image = item.get('image')
        self.swf = item.get('swf')
        self.date_added = item.get('dateAdded')
        self.campaign = item.get('campaignId')
        self.width = item.get('width')
        self.height = item.get('height')

    def _trim_by_words(self, str, max_len):
        ''' Обрезает строку ``str`` до длины не более ``max_len`` с учётом слов '''
        if len(str) <= max_len:
            return str
        trimmed_simple = str[:max_len]
        trimmed_by_words = trimmed_simple.rpartition(' ')[0]
        return u'%s…' % (trimmed_by_words or trimmed_simple)
