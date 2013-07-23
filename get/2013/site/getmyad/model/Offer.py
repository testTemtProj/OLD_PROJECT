# This Python file uses the following encoding: utf-8
import pymongo
from pylons import app_globals, config
import hashlib as h


class Offer(object):
    'Класс описывает рекламное предложение'
    
    def __init__(self, id):
        self.db = app_globals.db 
        self.id = id.lower()
        self.title = ''
        self.price = ''
        self.url = ''
        self.image = None
        self.swf = None
        self.description = ''
        self.date_added = None
        self.campaign = ''
        self.campaignTitle = ''
        self.uniqueHits = 1
        self.contextOnly = False
        self.retargeting = False
        self.keywords = []
        self.phrases = []
        self.exactly_phrases = []
        self.minus_words = []
        self.listAds = []
        self.category = ''
        self.isOnClick = True
        self.type = ''
        self.width = ''
        self.height = ''
        self.rating = ''
        self.hash = ''
        self.cost = 0
        self.accountId = ''

    def offerHashes(self):
        print

    def createOfferHash(self):
        offerHash = {}
        offerHash['guid'] = self.id
        offerHash['title'] = self.title
        offerHash['url'] = self.url
        offerHash['campaignId'] = self.campaign
        offerHash['cost'] = self.cost
        offerHash['price'] = self.price
        offerHash['dateAdded'] = self.date_added

        offerHash = str(h.md5(str(offerHash)).hexdigest())
        return offerHash
    
    def save(self):
        'Сохраняет предложение в базу данных'
        self.db.offer.update({'guid': self.id},
                                    {'$set': {'title': self._trim_by_words(self.title, 35),
                                              'price': self.price,
                                              'url': self.url,
                                              'image': self.image,
                                              'swf': self.swf,
                                              'description': self._trim_by_words(self.description, 70),
                                              'dateAdded': self.date_added,
                                              'campaignId': self.campaign,
                                              'campaignTitle': self.campaignTitle,
                                              'uniqueHits': self.uniqueHits,
                                              'contextOnly': self.contextOnly,
                                              'retargeting': self.retargeting,
                                              'keywords': self.keywords,
                                              'phrases': self.phrases,
                                              'exactly_phrases': self.exactly_phrases,
                                              'minus_words': self.minus_words,
                                              'listAds': self.listAds,
                                              'category': self.category,
                                              'isOnClick': self.isOnClick,
                                              'type': self.type,
                                              'width': self.width,
                                              'height': self.height,
                                              'rating': self.rating,
                                              'hash': self.hash,
                                              'cost': self.cost,
                                              'accountId': self.accountId
                                              }},
                                    upsert=True, safe=True)

    def update(self):
        'Обнавляет предложение в базу данных'
        self.db.offer.update({'guid': self.id, 'campaignId': self.campaign},
                                    {'$set': {'image': self.image,
                                              'swf': self.swf,
                                              'uniqueHits': self.uniqueHits,
                                              'contextOnly': self.contextOnly,
                                              'retargeting': self.retargeting,
                                              'listAds': self.listAds,
                                              'isOnClick': self.isOnClick,
                                              'type': self.type,
                                              'width': self.width,
                                              'height': self.height,
                                              'cost': self.cost,
                                              'accountId': self.accountId
                                              }},
                                    False)

    def _trim_by_words(self, str, max_len):
        ''' Обрезает строку ``str`` до длины не более ``max_len`` с учётом слов '''
        if len(str) <= max_len:
            return str
        trimmed_simple = str[:max_len]
        trimmed_by_words = trimmed_simple.rpartition(' ')[0]
        return u'%s…' % (trimmed_by_words or trimmed_simple)
