# coding: utf-8
import cProfile
from pprint import pprint
import urllib2
import base64
from urllib2 import URLError
import xml.etree.cElementTree as cElementTree
import json
import shutil
import hashlib as h
import pickle
import re
from trans import trans
from task_image import *
import datetime
import os
import uuid
import xmlrpc

from celery.task.sets import TaskSet
from celery.task.sets import subtask

import ConfigParser

PYLONS_CONFIG = "deploy.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config_multidownload = ConfigParser.ConfigParser()
config_multidownload.read(config_file)


ADLOAD_RPC_HOST = config_multidownload.get('app:main', 'adload_xml_rpc') 
print ADLOAD_RPC_HOST
CONNECT_TO_MONGO = config_multidownload.get('app:main', 'mongo_host')
db = config_multidownload.get('app:main', 'mongo_database')
COUNTRIES = pickle.load(file( '%s/../../%s' % (os.path.dirname(__file__), config_multidownload.get('app:main', 'path_to_COUNTRIES')), 'r+'))
PATH_TO_NOT_VALID = '%s/../../%s' % (os.path.dirname(__file__), config_multidownload.get('app:main', 'path_to_NOT_VALID'))
PATH = '%s/../../%s' % (os.path.dirname(__file__), config_multidownload.get('app:main', 'path_to_YML'))
PATH_TO_OLD_XML = '%s/../../%s' % (os.path.dirname(__file__), config_multidownload.get('app:main', 'path_to_OLD_YML'))
ARHIVES = '%s/../../%s' % (os.path.dirname(__file__), config_multidownload.get('app:main', 'path_to_ARHIVES'))
HASHES = '%s/../../%s' % (os.path.dirname(__file__), config_multidownload.get('app:main', 'path_to_hashes'))

ARHIVES_TYPE = ('.gz', 'zip', 'rar')
CURRENCY_TYPE = (
    'AMD', 'AUD', 'AZM', 'BGL', 'BRL', 'BYR', 'CAD', 'CHF', 'CLP', 'CNY',
    'CYP', 'CZK', 'DKK', 'ECS', 'EEK', 'EGP', 'EUR', 'GBP', 'GEL',
    'HKD', 'HRK', 'HUF', 'ILS', 'INR', 'IQD', 'IRR', 'ISK', 'JPY', 'KGS',
    'KPW', 'KRW', 'KWD', 'KZT', 'LBP', 'LTL', 'LVL', 'LYD', 'MDL',
    'MNT', 'MTL', 'MXN', 'NOK', 'NZD', 'PEN', 'PKR', 'PLZ', 'ROL', 'RUR',
    'SAR', 'SEK', 'SGD', 'SIT', 'SKK', 'SYP', 'TJS', 'TMM', 'TRL',
    'TWD', 'UAH', 'USD', 'UZS', 'VND', 'XAG', 'XAU', 'XOF', 'XPD', 'XPT',
    'NONE')

DEFAULT_CURRENCY_RATES = \
    {'UAH': {'UAH': 1, 'USD': 0.125, 'EUR': 00.09, 'RUB': 00.24},
     'USD': {'USD': 1, 'UAH': 7.980, 'EUR': 00.70, 'RUB': 28.00},
     'RUB': {'RUB': 1, 'USD': 0.040, 'EUR': 00.02, 'UAH': 04.08},
     'EUR': {'EUR': 1, 'USD': 1.430, 'UAH': 11.46, 'RUB': 40.20}
}
LANGUAGE_TYPE = ('ru', 'ua', 'en', 'rus', 'uah', 'eng')

none_fields = (
    'url', 'price', 'currencyId', 'categoryId', 'picture', 'vendor',
    'vendorCode', 'sales_notes', 'country_of_origin',
    'barcode', 'model')
vendor_model_fields = (
    'url', 'price', 'currencyId', 'categoryId', 'picture', 'typePrefix',
    'vendor', 'vendorCode', 'sales_notes',
    'country_of_origin', 'barcode', 'model')
book_fields = (
'url', 'price', 'currencyId', 'categoryId', 'picture', 'ISBN', 'author')
audiobook_fields = (
'url', 'price', 'currencyId', 'categoryId', 'picture', 'ISBN', 'author')
artist_title_fields = (
'url', 'price', 'currencyId', 'categoryId', 'picture', 'barcode')
tour_title_fields = ('url', 'price', 'currencyId', 'categoryId', 'picture')
event_ticket_fields = (
'url', 'price', 'currencyId', 'categoryId', 'place', 'date', 'picture')

book_escape = (
    'name', 'publisher', 'series', 'year', 'volume', 'part', 'language',
    'binding', 'page_extent', 'downloadable',
    'table_of_contents')
audiobook_escape = (
    'name', 'publisher', 'year', 'language', 'performed_by',
    'performance_type', 'storage', 'format', 'recording_length',
    'table_of_contents', 'downloadable')
artist_title_escape = ['media', 'director', 'year']
tour_escape = (
'worldRegion', 'country', 'region', 'name', 'hotel_stars', 'room', 'meal')
event_ticket_escape = ['hall_part', 'is_premiere', 'is_kids', 'hall']

delivery = ['delivery', 'store', 'pickup', 'local_delivery_cost']

def clear_description(string):
    """
        Функция для очистки строки от HTML тегов

        Получает:
            string - строка из которой нужно убрать HTML теги

        Возвращает:
           string - строка очищеная от HTML тегов
    """
    try:
        string = string.replace('&amp;lt;','<').replace('&amp;gt;','>')
        re_tags = re.compile("(<[^>]*>)", re.IGNORECASE|re.UNICODE)
        string = re.sub(re_tags, "", string)
        return string
    except:
        return ''

def normalize_tag(tag):
    if tag[0] == "{":
        prefix, tag = tag[1:].split("}")
        return tag
    return tag



def get_vendors():
    db = pymongo.Connection(CONNECT_TO_MONGO)[db]
    vendors = []
    for x in db.Yottos_venders.find():
        vendors.append(x['name'])
    id = 0
    for offer in db.Offers.find():
        if 'vendor' in offer:
            if offer['vendor'] not in vendors:
                vendors.append(offer['vendor'])
                tmp = {}
                tmp['id'] = id
                tmp['name'] = offer['vendor']
                db.Yottos_venders.insert(tmp)
                id += 1


def unzip(path, file, marketId, arhType=None):
    if arhType != None:
        os.system("tar xvzf " + path + file)
    else:
        os.system("7z e " + path + file)
    os.remove(path + file)
    dirList = os.listdir('.')

    for fname in dirList:
        if fname[len(fname) - 3:len(fname)] == 'xml':
            save_to = fname
            break
            
    os.rename(save_to, str(marketId) + '.xml')
    save = str(marketId) + '.xml'
    shutil.copy(save, PATH)
    os.remove(save)
    return save


class Download():
    def __init__(self, url, id, save_to='None'):
        self.url = url
        self.save_to = save_to
        self.shopId = id

        self.DB = pymongo.Connection(host=CONNECT_TO_MONGO)[db]
        self.first = False
        self.eva = {
            'state': 'parsing',
            'message': '',
            'added': 0,
            'deleted': 0,
            'not_valid': 0,
            'started':datetime.datetime.now()
        }

        if self.DB.Offers.find({'shopId': self.shopId}).count() == 0:
            self.first = True

        tmp = self.DB.Market.find_one({'id': int(id)})

        if tmp is None:
            raise("No market #%s found in database" % (id))

        self.market_url = None
        self.market_name = None

        self.market_url = tmp['urlMarket']
        self.market_name = tmp['title'] if 'title' in tmp else tmp['urlMarket']

    def saveData(self, data, filename):
        file = open(filename, 'w')
        pickle.dump(data, file)
        file.close()

    def restoreData(self, filename):
        if os.path.exists(filename):
            file = open(filename, 'r')
            data = pickle.load(file)
            file.close()
            return data
        else:
            return []
    def set_state(self):
        """Сохранения состояния парсинга в базу"""
        self.DB.Market.update({'id': self.shopId}, {"$set": {'state': self.eva}})
        
    def check_changes_in_xml(self, file):
        try:
            old_xml = PATH_TO_OLD_XML + file
            new_xml = PATH + file
            old_xml_date = None
            new_xml_date = None
            for  event, elem in cElementTree.iterparse(old_xml):

                elem.tag = normalize_tag(elem.tag)

                if elem.tag == 'yml_catalog':
                    old_xml_date = elem.items()[0][1]
                    elem.clear()

            for  event, elem in cElementTree.iterparse(new_xml):

                elem.tag = normalize_tag(elem.tag)

                if elem.tag == 'yml_catalog':
                    new_xml_date = elem.items()[0][1]
                    elem.clear()

            if os.path.getsize(old_xml) != os.path.getsize(new_xml) or old_xml_date != new_xml_date:
                return new_xml_date
            else:
                return False
        except:
            return True

    def _offer_validator(self, offer, offer_type):
        validate_templates = {
            'vendor.model': ['price', 'currencyId', 'categoryId', 'vendor',
                             'model'], \
            'book': ['price', 'currencyId', 'categoryId', 'name'], \
            'audiobook': ['price', 'currencyId', 'categoryId', 'name'], \
            'artist.title': ['price', 'currencyId', 'categoryId', 'title'], \
            'tour': ['price', 'currencyId', 'categoryId', 'name', 'included',
                     'days'], \
            'event-ticket': ['price', 'currencyId', 'categoryId', 'name',
                             'place', 'date'], \
            }

        if offer_type in validate_templates:
            valid_tags = validate_templates[offer_type]
        else:
            valid_tags = ['categoryId', 'name']

        for tag in offer.getchildren():

            tag.tag = normalize_tag(tag.tag)

            not_valid = self._field_validator(tag.tag, tag.text)
            if not_valid != True:
                return not_valid

            if tag.tag in valid_tags:
                valid_tags.remove(tag.tag)

        if not len(valid_tags):
            return True

        return valid_tags

    def _field_validator(self, tag, value):

        tag = normalize_tag(tag)

        if value is None:
            value = ''

        if isinstance(value, str):
            value = value.strip()

        if tag == 'country_of_origin':
            if not value in COUNTRIES:
                return tag

        elif tag == 'vendor':
            if value.isdigit():
                return tag

        elif tag == 'url':
            if sys.getsizeof(value) > 2000:
                return tag

        elif tag  in ('delivery', 'pickup', 'downloadable', 'store',
                      'manufacturer_warranty'):
            if value not in ('true', 'false'):
                return tag

        elif tag == 'currencyId':
            if value.upper() not in CURRENCY_TYPE:
                return tag

        elif tag == 'categoryId':
            if not (value.isdigit() and (len(value) <= 9 and int(value) > 0)):
                return tag

        elif tag in ('local_delivery_cost', 'page_extent', 'days'):
            if not (value.isdigit() and int(value) > 0):
                return tag

        elif tag == 'year':
            if not (value.isdigit() and len(value) == 4):
                return tag

        elif tag in ('is_kids', 'is_premiere'):
            if value not in ('true', 'false', '1', '0'):
                return tag

        elif tag == 'barcode':
            if len(value) not in (8, 12, 13):
                return tag

        elif tag == 'sales_notes':
            if len(value) > 100:
                return tag

        elif tag == ('model', 'name', 'title'):
            if value.isdigit():
                return tag

        elif tag == 'language':
            if value.lower() not in LANGUAGE_TYPE:
                return tag

        return True

    def get_offers(self, file):
        count = 0
        vendors = []
        lot_id = None
        to_add = []
        currencies = []
        tempo_hashes = []
        images_list = []
        task_list = []    
        self.eva['not_valid'] = 0
        self.DB.Market.update({'id': int(self.shopId)},
                {"$set": {'lot_delete': ''}})
        self.DB.Market.update({'id': int(self.shopId)},
                {"$set": {'lot_add': ''}})

        for x in self.DB.Vendors.find():
            vendors.append(x)

        hashes = self.restoreData(HASHES + str(self.shopId))

        market = self.DB.Market.find_one({'id': self.shopId})
        if not 'time_setting' in market:
            self.DB.Market.update({'id': self.shopId}, {
                "$set": {
                    'time_setting': {'interval': u'час', 'interval_count': 1,
                                     'Params': [{"time": "00:00"}]}}})

        log_file = open(PATH_TO_NOT_VALID + str(self.shopId) + '.txt', 'w+')

        offers_processing = False

        try:
            for event, elem in cElementTree.iterparse(file, events=("start", "end")):

                elem.tag = normalize_tag(elem.tag)

                if elem.tag == 'offers' and event == 'start':
                    offers_processing = True
                    continue

                if elem.tag == 'offers' and event == "end":                    
                    _list_offers = list(elem)
                    _total_offers = len(_list_offers)
                    current_offer = 0
                    for offer_element in _list_offers:                                                

                        offer_element.tag = normalize_tag(offer_element.tag)

                        if offer_element.tag == "offer":
                            
                            current_offer += 1
                            #print "#%s" % current_offer
                            if current_offer % 100 == 0:                                
                                self.eva['progress'] = {'state':'parsing_offers', 'current':current_offer, 'total':_total_offers}
                                self.set_state()
                            
                            offer_id = ''
                            lot = {}
                            lot['type'] = 'None'
                            lot['shopId'] = self.shopId

                            offer_type = None
                            for option, value in offer_element.items():
                                if option == 'type':
                                    offer_type = value
                                elif option == 'id':
                                    offer_id = value
                                    dt = datetime.datetime.now()
                                    lot_id = str(value) + str(
                                        self.shopId) + str(
                                        dt.strftime('%m%d%H'))
                                else:
                                    lot[option] = value

                            validation_result = self._offer_validator(
                                offer_element, offer_type)
                            if validation_result is not True:
                                self.eva['not_valid'] += 1
                                log_file.write(offer_id + " " + str(
                                    validation_result) + '\n')
                                offer_element.clear()
                                continue

                            deliv = []
                            for tag in list(offer_element):

                                tag.tag = normalize_tag(tag.tag)

                                if tag.tag in delivery:
                                    if tag.tag == 'local_delivery_cost':
                                        deliv.append({tag.tag: tag.text})
                                    elif tag.text == 'true':
                                        deliv.append({tag.tag: True})
                                    else:
                                        deliv.append({tag.tag: False})

                            lot['delivery'] = deliv

                            if offer_type == 'vendor.model':
                                lot['type'] = 'vendor.model'

                                is_vendor = False
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag not in delivery:
                                        if tag.tag == 'vendor' and \
                                           tag.text != '*':
                                            lot['vendor'] = tag.text
                                            is_vendor = True
                                        elif tag.tag == 'model':
                                            lot['title'] = tag.text
                                            if lot['title'] is None:
                                                is_vendor = False
                                        elif tag.tag == \
                                             'manufacturer_warranty':
                                            lot['warranty'] = tag.text
                                        elif tag.tag == 'description':
                                            lot[
                                            'description'] = clear_description(
                                                tag.text)
                                        elif tag.tag == 'picture':
                                            if tag.text:                                                                                                                                  
                                                lot['picture'] = tag.text.replace('/n', '').replace(' ', '')
                                            
                                        elif tag.tag in vendor_model_fields:
                                            lot[tag.tag] = tag.text
                                            
                                        #TODO: ГРЯЗНЫЙ хак от пустых полей
                                        if tag.text is None:
                                            lot[tag.tag] = 'None'
                                if not is_vendor:
                                    lot['vendor'] = 'None vendor'
                                elif lot['title'].find(lot['vendor']) == -1:
                                    lot['title'] = lot['vendor'] + " " + \
                                                   lot['title']

                            elif offer_type == 'book':
                                lot['type'] = 'book'

                                title = ['', '']
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag == 'author':
                                        title[0] = tag.text
                                    if tag.tag == 'name':
                                        title[1] = '"' + tag.text + '"'
                                lot['title'] = ' '.join(title).strip()

                                params = {}
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag not in delivery:
                                        if tag.tag in book_escape:
                                            params[tag.tag] = tag.text
                                        elif tag.tag == 'description':
                                            lot[
                                            'description'] = clear_description(
                                                tag.text)
                                        elif tag.tag == 'picture':
                                            if tag.text:
                                                lot['picture'] = tag.text.replace('/n', '').replace(' ', '')
                                        elif tag.tag in book_fields:
                                            lot[tag.tag] = tag.text
                                lot['params'] = params
                            elif offer_type == 'audiobook':
                                lot['type'] = offer_type

                                title = ['', '']
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag == 'author':
                                        title[0] = tag.text
                                    if tag.tag == 'name':
                                        title[1] = '"' + tag.text + '"'

                                lot['title'] = ' '.join(title).strip()

                                params = {}
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag not in delivery:
                                        if tag.tag in audiobook_escape:
                                            params[tag.tag] = tag.text
                                        elif tag.tag == 'description':
                                            lot[
                                            'description'] = clear_description(
                                                tag.text)
                                        elif tag.tag == 'picture':
                                            if tag.text:
                                                lot['picture'] = tag.text.replace('/n', '').replace(' ', '')
                                        elif tag.tag in audiobook_fields:
                                            lot[tag.tag] = tag.text

                                lot['params'] = params

                            elif offer_type == 'artist.title':
                                lot['type'] = 'artist.title'

                                artist = ''
                                title = ''
                                original_name = ''
                                starring = ''

                                params = {}
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag not in delivery:
                                        if tag.tag in artist_title_escape:
                                            params[tag.tag] = tag.text
                                        elif tag.tag == 'starring':
                                            starring = tag.text
                                        elif tag.tag == 'artist':
                                            artist = tag.text
                                        elif tag.tag == 'title':
                                            title = tag.text
                                        elif tag.tag == 'originalName':
                                            original_name = '"' + \
                                                            tag.text + \
                                                            '"'
                                        elif tag.tag == 'picture':
                                            if tag.text:
                                                lot['picture'] = tag.text.replace('/n', '').replace(' ', '')
                                        elif tag.tag == 'country':
                                            lot['country_of_origin'] = tag.text
                                        elif tag.tag == 'description':
                                            lot[
                                            'description'] = clear_description(
                                                tag.text)
                                        elif tag.tag in artist_title_fields:
                                            lot[tag.tag] = tag.text

                                lot['author'] = ' '.join(
                                    [artist, starring]).strip()
                                lot['title'] = ' '.join([title, original_name,
                                                         lot[
                                                            'author'
                                                         ]]).strip().replace(
                                                            '  ',
                                                            ' ')

                                lot['params'] = params

                            elif offer_type == 'tour':
                                lot['type'] = 'tour'
                                title = {}
                                params = {}
                                params_fields = (
                                    'worldRegion', 'country', 'region', 'name',
                                    'hotel_stars', 'room', 'meal', 'included',
                                    'days', 'transport')

                                lot['date'] = []
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag not in delivery:
                                        if tag.tag in tour_escape:
                                            if tag.text is not None:
                                                title[tour_escape.index(
                                                    tag.tag)] = tag.text
                                        if tag.tag in params_fields:
                                            params[tag.tag] = tag.text
                                        if tag.tag == 'country':
                                            lot['country_of_origin'] = tag.text
                                        if tag.tag == 'place':
                                            lot['region'] = tag.text
                                        elif tag.tag == 'dataTour':
                                            lot['date'].append(tag.text)
                                        elif tag.tag == 'picture':
                                            if tag.text:
                                                lot['picture'] = tag.text.replace('/n', '').replace(' ', '')
                                        elif tag.tag == 'description':
                                            lot[
                                            'description'] = clear_description(
                                                tag.text)
                                        elif tag.tag in tour_title_fields:
                                            lot[tag.tag] = tag.text

                                tempo_title = []
                                for key in sorted(title):
                                    raw_title = title[key].strip()
                                    if len(raw_title):
                                        tempo_title.append(raw_title)

                                lot['title'] = ' '.join(tempo_title)

                                lot['params'] = params

                            elif offer_type == 'event-ticket':
                                lot['type'] = 'event-ticket'
                                params = {}
                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag not in delivery:
                                        if tag.tag in event_ticket_escape:
                                            if tag.tag == 'hall':
                                                for option, value in \
                                                    tag.items():
                                                    if option == 'plan':
                                                        params[
                                                            'hall'
                                                        ] = \
                            '<a href = "' + value + '">' + tag.text + '</a>'
                                            else:
                                                params[tag.tag] = tag.text
                                        elif tag.tag == 'name':
                                            lot['title'] = tag.text
                                        elif tag.tag == 'picture':
                                            if tag.text:
                                                lot['picture'] = tag.text.replace('/n', '').replace(' ', '')
                                        elif tag.tag == 'description':
                                            lot[
                                            'description'] = clear_description(
                                                tag.text)
                                        elif tag.tag in event_ticket_fields:
                                            lot[tag.tag] = tag.text

                                lot['params'] = params

                            else:
                                lot['params'] = {}
                                is_vendor = False

                                for tag in list(offer_element):

                                    tag.tag = normalize_tag(tag.tag)

                                    if tag.tag not in delivery:
                                        if tag.tag == 'vendor' and \
                                           tag.text != '*':
                                            lot['vendor'] = tag.text
                                            is_vendor = True
                                        elif tag.tag == 'name':
                                            lot['title'] = tag.text
                                        elif tag.tag == 'picture':
                                            if tag.text:
                                                lot['picture'] = tag.text.replace('/n', '').replace(' ', '')
                                        elif tag.tag == 'description':
                                            lot[
                                            'description'] = clear_description(
                                                tag.text)
                                        elif tag.tag in none_fields:
                                            lot[tag.tag] = tag.text

                                if 'vendor' in lot and 'title' in lot:
                                    if lot['vendor'] and lot['vendor'] in lot['title']:
                                        lot['title'] = lot['vendor'] + lot['title']

                                if is_vendor:
                                    vendor_id = self.DB.Vendors.find_one(
                                            {'name': lot['vendor']},
                                            {'id': 1})
                                    
                                    for model_item in self.DB.Model.find(
                                            {'vendor_id': vendor_id}):
                                        if lot['title'].find(
                                            model_item['name']) != -1:
                                            lot['model'] = model_item['name']
                                            model_id = self.DB.Model.find_one({
                                                'name': model_item['name']})[
                                                       'model_id']
                                            for code \
                                            in self.DB.VendorCode.find(
                                                    {'id': model_id}):
                                                if lot['title'].find(
                                                    code['name']) != -1:
                                                    lot['vendorCode'] = code[
                                                                        'name']
                                else:
                                    for vendor in vendors:
                                        if lot['title'].find(
                                            vendor['name']) != -1:
                                            for model_item \
                                            in self.DB.Model.find(
                                                    {'vendor_id': vendor[
                                                                  'id']}):
                                                if lot['title'].find(
                                                    model_item['name']) != -1:
                                                    lot['vendor'] = vendor[
                                                                    'name']
                                                    lot['model'] = model_item[
                                                                   'name']
                                                    model_id = \
                                                    self.DB.Model.find_one({
                                                        'name': model_item[
                                                                'name']})[
                                                    'model_id']
                                                    for code \
                                                    in self.DB.VendorCode.find(
                                                            {'id': model_id}):
                                                        if lot['title'].find(
                                                            code[
                                                                'name'
                                                            ]) != -1:
                                                            lot[
                                                                'vendorCode'
                                                            ] = code['name']

                            if lot['currencyId'] is None \
                            or lot['currencyId'] == 'NONE':
                                currency_id = 'UAH'
                            else:
                                currency_id = lot['currencyId'].strip()

                            if not currency_id in DEFAULT_CURRENCY_RATES:
# TODO: Добавить константы синонимов и переназначать их
                                if currency_id == 'RUR':
                                    currency_id = 'RUB'

                            lot['currencyId'] = currency_id
                            try:
                                lot['price'] = float(lot['price'].replace(',', '.'))
                            except:
                                lot['price'] = float(0)

                            for rate in DEFAULT_CURRENCY_RATES:
                                lot[rate] = float(0)

                            if currency_id in DEFAULT_CURRENCY_RATES:
                                rates = DEFAULT_CURRENCY_RATES[currency_id]
                                
#TODO: Отключены курсы магазина. Обратите внимание на разделитель цены
# ,(запятая) или .(точка)
#for currency in currencies:
#    if rates.has_key(currency['id']) and currency.has_key('rate') :
#        currency['rate'] = currency['rate'].replace(',', '.')
#        try:
#            rate = float(currency['rate'])
#            rates[currency['id']] = rate
#        except:
#            continue

                                for rate in rates:
                                    lot[rate] = float(lot['price']) * float(rates[rate])

                            offer_hash = str(h.md5(str(lot)).hexdigest())

                            lot['id'] = lot_id
                            lot['uuid'] = uuid.uuid4()
                            lot['dateAdded'] = datetime.datetime.now()
                            lot['offer_hash'] = offer_hash
                            lot['categoryId'] = int(lot['categoryId'])
                            
 
                            tempo_hashes.append(offer_hash)
                            if self.DB.Offers.find({'shopId': self.shopId,
                                            'offer_hash': offer_hash}).count():
                                if offer_hash in hashes:
                                    hashes.remove(offer_hash)
                            else:
                                if lot.has_key('picture') and lot['picture']!='None':
                                    dt = datetime.datetime.now()
                                    path = "%s/%s/%s/%s" %(dt.year, dt.month, dt.day, lot['offer_hash'][-3:])
                                    images_list.append({'offer_hash':lot['offer_hash'],
                                                        'url':lot['picture'],
                                                        'path':path})
                                self.DB.Offers.insert(lot)
                                to_add.append(lot_id)

                if offers_processing:
                    continue

                if elem.tag == "name" and event == "end":
                    translited_title = unicode(elem.text).encode('trans').lower()
                    
                    if len(translited_title) < 2:
                        translited_title = market['urlMarket']

                    transformed_title = re.compile(r'[^\w+]').sub('-',
                                                              translited_title)

                    unique = True

                    for occurence in self.DB.Market.find(
                            {'transformedTitle': transformed_title}):
                        unique = unique and (occurence['id'] != self.shopId)

                    if unique == False:
                        transformed_title = "%s-%s" % (
                        transformed_title, self.shopId)
                        
                    try:
                        market_name = elem.text.decode('utf8')
                    except:
                        market_name = elem.text
                        
                    if self.market_name != market_name:
                        self.DB.Market.update({'id': int(self.shopId)}, {"$set": {'title': market_name}})

                    self.DB.Market.update({'id': int(self.shopId)}, {"$set": {'transformedTitle': transformed_title}})

                    continue

                if elem.tag == "url" and event == "end":
                    if self.market_url != elem.text:
                        self.DB.Market.update({'id': int(self.shopId)},
                                {"$set": {'urlMarket': elem.text}})
                    continue

                if elem.tag == "currencies" and event == "end":
                    for tag in list(elem):
                        currency = {}
                        for option, value in tag.items():
                            currency[option] = value
                        currencies.append(currency)
                    continue

                if elem.tag == 'offer' and event == "end":
                    break

        except SyntaxError as message:
            self.eva['not_valid'] += 1
            pass

        self.DB.Market.update({'id': int(self.shopId)},
                {"$set": {'lot_add': to_add}})
        self.saveData(tempo_hashes, HASHES + str(self.shopId))
        self.del_lots(hashes)

        log_file.close()

        self.eva['added'] = len(to_add)
        
   
        for image in images_list:
            task_list.append(download_image.subtask(args=[image], options={'queue':"image_tasks", 'routing_key':"image.process"}))
        try:
            task_set = TaskSet(task_list)
            self.eva['progress'] = {'state':'parsing_images'}
            self.set_state()      
            tasks = task_set.apply_async()
            print 'iterating image results %s' % self.shopId
            for image in iter(tasks):
                if image['ok']:
                    image['key']['shopId'] = self.shopId
                    self.DB.Offers.update(image['key'], {'$set':{'images':image['url']}})

            if tasks.ready() and tasks.successful():
                self.eva['state'] = {'state':'complete_images'}            
                self.set_state()

        except Exception, ex:
            print ex

        return len(to_add)

    def del_lots(self, hashes):
        ids = []
        for offer in self.DB.Offers.find(
                {'shopId': self.shopId, 'offer_hash': {'$in': hashes}}):
            ids.append(offer['id'])

        self.DB.Offers.remove(
                {'shopId': self.shopId, 'offer_hash': {'$in': hashes}})
        self.DB.Market.update({'id': int(self.shopId)},
                {"$set": {'lot_delete': ids}})

        self.eva['deleted'] = len(ids)

    def get_categories(self, file):        
        self.eva['progress'] = {'state':'parsing_categories'}
        self.set_state()
        count = 0
        categories = []

        try:
            for event, elem in cElementTree.iterparse(file):
                elem.tag = normalize_tag(elem.tag)
                if elem.tag == 'category' and event == 'end':
                    cat = {}
                    cat['name'] = elem.text
                    for item in elem.items():
                        cat[item[0]] = item[1]
                    categories.append(cat)
                    count += 1
                elem.clear()
        except SyntaxError as message:
            self.eva['state'] = 'error'
            self.eva['message'] = 'Syntax error in categories: %s' % (message)
            raise Exception('SYNTAX', message)
        except:
            self.eva['state'] = 'error'
            self.eva['message'] = 'Unknown syntax error in categories'
            raise Exception('SYNTAX', 'UNKNOWN')

        t = h.md5(str(categories))
        hash = str(t.hexdigest())
        market = self.DB.Market.find_one({'id': int(self.shopId)})
        category_hash = None
        if 'category_hash' in market:
            category_hash = market['category_hash']

        if hash != category_hash:
            self.eva['categories'] = count
            self.DB.Market.update(
                    {"id": self.shopId},
                    {"$set":
                             {'Categories': categories,
                              'category_hash': hash}
                    },
                    upsert=True)
        else:
            self.eva['categories'] = count
        return 'ok'

    def run(self):
        is_auth = False
        market = self.DB.Market.find_one({'id': int(self.shopId)})
        self.eva['state'] = 'parsing'
        self.eva['progress'] = {'state':'download_yml'}
        self.set_state()#{'state':'parsing', 'progress':{'state':'download_yml'}, 'started':datetime.datetime.now()})
        started = datetime.datetime.now()
        
        if market is not None:
            if 'login' in market:
                request = urllib2.Request(self.url)
                base64string = base64.encodestring(
                    '%s:%s' % (market['login'], market['password'])).replace(
                    '\n', '')
                request.add_header("Authorization", "Basic %s" % base64string)
                output = open(PATH + str(self.shopId) + '.xml', 'wb')
                try:
                    result = urllib2.urlopen(request)
                    output.write(result.read())
                except URLError, e:
                    self.eva['finished'] = datetime.datetime.now()
                    self.eva['state'] = 'error'
                    if hasattr(e, 'code'): 
                        if e.code == 404:
                            self.eva['message'] = u"Файл не найден %s " % (self.url)
                        else:
                            self.eva['message'] = u"Ошибка во время чтения файла %s " % (self.url)
                    else:
                        self.eva['message'] = str(e.reason)

                    raise Exception("ERROR", self.eva['message'])
                except:
                    self.eva['finished'] = datetime.datetime.now()
                    self.eva['state'] = 'error'
                    if self.url:
                        self.eva['message'] = u"Ошибка во время чтения файла %s " % (self.url)
                    else:
                        self.eva['message'] = u"Для магазина не указан файл каталога"
                    raise Exception("ERROR", self.eva['message'])
                finally:
                    output.close()
                is_auth = True

        if not is_auth:
            a = urllib2.urlopen(self.url)
            code = a.getcode()
        else:
            code = 200

        if code < 400:
            if self.save_to == 'None':
                save_to = str(self.shopId) + '.xml'
                if os.path.basename(self.url[len(self.url) - 3:len(self.url)]) in ARHIVES_TYPE:
                    file = os.path.basename(self.url)
                    request = urllib2.Request(self.url)
                    result = urllib2.urlopen(request)
                    output = open(ARHIVES + file, 'wb')
                    output.write(result.read())
                    output.close()
                    self.eva['progress'] = {'state':'unpacking'}                    
                    self.set_state()
                    if os.path.basename(
                        self.url[len(self.url) - 6:len(self.url)]) == 'tar.gz':
                        save_to = unzip(ARHIVES, file, self.shopId,
                                        arhType='tar.gz')
                    else:
                        save_to = unzip(ARHIVES, file, self.shopId, None)
            else:
                save_to = self.save_to

            if self.save_to == 'None' and os.path.basename(self.url[len(self.url) - 3:len(self.url)]) not in ARHIVES_TYPE:
                if self.url[0:7] == 'http://':
                    if not is_auth:
                        request = urllib2.Request(self.url)
                        result = urllib2.urlopen(request)
                        output = open(PATH + save_to, 'wb')
                        output.write(result.read())
                        output.close()

                else:
                    if not is_auth:
                        request = urllib2.Request('http://' + self.url)
                        result = urllib2.urlopen(request)
                        output = open(PATH + save_to, 'wb')
                        output.write(result.read())
                        output.close()

            file_date = self.check_changes_in_xml(save_to)
            
            if file_date:
                self.DB.Market.update({'id': self.shopId}, {"$set": {'file_date': file_date}})
                self.get_categories(PATH + save_to)
                count = self.get_offers(PATH + save_to)
                self.eva['added'] = count
                shutil.copy(PATH + save_to, PATH_TO_OLD_XML)
            else:
                self.eva['state'] = "finished"
                self.eva['finished'] = datetime.datetime.now()
                self.eva['progress'] = ""
                self.eva['message'] = ''
                self.eva['added'] = 0
                self.eva['categories'] = 0
                self.eva['deleted'] = 0
                self.eva['not_valid'] = 0

            try:
                self.eva['state'] = "finished"
                self.eva['progress'] = ""
                self.eva['finished'] = datetime.datetime.now()
                self.set_state()
                os.remove(PATH + save_to)
            except Exception, message:
                print message
                pass
        else:
            self.eva['message'] = "YML file not found by url: %s " % (self.url)
    
        self.eva['state'] = "finished"
        self.eva['progress'] = ""
        self.eva['finished'] = datetime.datetime.now()
        self.set_state()        
        
        return 'ok'


class Parser():
    def __init__(self):
        self.db = pymongo.Connection(host=CONNECT_TO_MONGO)[db]

    def _offer_validator(self, offer, offer_type):
        validate_templates = {
            'vendor.model': ['price', 'currencyId', 'categoryId', 'vendor',
                             'model'], \
            'book': ['price', 'currencyId', 'categoryId', 'name'], \
            'audiobook': ['price', 'currencyId', 'categoryId', 'name'], \
            'artist.title': ['price', 'currencyId', 'categoryId', 'title'], \
            'tour': ['price', 'currencyId', 'categoryId', 'name', 'included',
                     'days'], \
            'event-ticket': ['price', 'currencyId', 'categoryId', 'name',
                             'place', 'date'], \
            }

        if offer_type in validate_templates:
            valid_tags = validate_templates[offer_type]
        else:
            valid_tags = ['categoryId', 'name']

        for tag in offer.getchildren():
            not_valid = self._field_validator(tag.tag, tag.text)
            if not_valid != True:
                return not_valid

            if tag.tag in valid_tags:
                valid_tags.remove(tag.tag)

        if not len(valid_tags):
            return True

        return valid_tags

    def _field_validator(self, tag, value):
        """
            Функция для валидации полей товара

            Получает:
                tag - название поля
                value - значение поля

            Возвращает:
                True||False - True - вылидно, False - не валидно
        """

        if value is None:
            value = ''

        if isinstance(value, str):
            value = value.strip()

        if tag == 'country_of_origin':
            if not value in COUNTRIES:
                return tag

        elif tag == 'vendor':
            if value.isdigit():
                return tag

        elif tag == 'url':
            if sys.getsizeof(value) > 2000:
                return tag

        elif tag  in ('delivery', 'pickup', 'downloadable', 'store',
                      'manufacturer_warranty'):
            if value not in ('true', 'false'):
                return tag

        elif tag == 'currencyId':
            if value.upper() not in CURRENCY_TYPE:
                return tag

        elif tag == 'categoryId':
            if not (value.isdigit() and (len(value) <= 9 and int(value) > 0)):
                return tag

        elif tag in ('local_delivery_cost', 'page_extent', 'days'):
            if not (value.isdigit() and int(value) > 0):
                return tag

        elif tag == 'year':
            if not (value.isdigit() and len(value) == 4):
                return tag

        elif tag in ('is_kids', 'is_premiere'):
            if value not in ('true', 'false', '1', '0'):
                return tag

        elif tag == 'barcode':
            if len(value) not in (8, 12, 13):
                return tag

        elif tag == 'sales_notes':
            if len(value) > 100:
                return tag

        elif tag == ('model', 'name', 'title'):
            if value.isdigit():
                return tag

        elif tag == 'language':
            if value.lower() not in LANGUAGE_TYPE:
                return tag

        return True

    def test(self, url, is_file=False):
        """
            Функция для проверки файла выгрузки на валидность

            Получает:
                url - url ссылка на файл выгрузки или имя файла
                is_file - True если url - имя файла, False - если url
                          ссылка поумолчанию равна False
        """

        not_valid_offers = []
        not_valid_fields = []
        result = {}
        result['message'] = ''
        try:
            if not is_file:
                webFile = urllib2.urlopen(url)
                filename = str(uuid.uuid4())
                localFile = file(filename, 'w+')
                localFile.write(webFile.read())
                webFile.close()
                localFile.close()
                localFile = file(filename, 'r+')
            else:
                localFile = open(url)

            for  event, elem in cElementTree.iterparse(localFile):
                if elem.tag == 'offer' and event == 'end':
                    offer_type = None
                    for option, value in elem.items():
                        if option == 'type':
                            offer_type = value
                        elif option == 'id':
                            offer_id = value
                    try:
                        validator_result = self._offer_validator(elem,
                                                                 offer_type)
                        if validator_result is not True:
                            err_msg = "Ид товара: %s, Не валидный тег: %s" % (
                            offer_id, validator_result)
                            not_valid_offers.append(err_msg)

                    except Exception, message:
                        result['status'] = 'error'
                        result['message'] = message
                        continue

        except Exception, message:
            result['status'] = 'error'
            result['message'] = message
            
        result['not_valid_offers'] = not_valid_offers
        result['not_valid_fields'] = not_valid_fields

        return result

    def parse_by_url(self, url):
        """
            Функция для распарсивания по ссылке на файл. Добавляет новый
            магазин исходя из данных в файле выгрузки

            Получает:
                url - ссылка на файл выгрузки
        """

        try:
            marketId = int(
                self.db.Market.find().sort('id', -1).limit(1).next()['id']) + 1
        except:
            marketId = 1
        market = {}

        save_to = str(marketId) + '.xml'
        if os.path.basename(url[len(url) - 3:len(url)]) in ARHIVES_TYPE:
            file = os.path.basename(url)
            #urllib.urlretrieve(url, ARHIVES + file)

            request = urllib2.Request(url)
            result = urllib2.urlopen(request)
            output = open(ARHIVES + file, 'wb')
            output.write(result.read())
            output.close()

            if os.path.basename(
                self.url[len(self.url) - 6:len(self.url)]) == 'tar.gz':
                save_to = unzip(ARHIVES, save_to, self.shopId, 'tar.gz')
            else:
                save_to = unzip(ARHIVES, save_to, self.shopId, None)
        else:
            #urllib.urlretrieve(url, PATH+save_to)
            request = urllib2.Request(url)
            result = urllib2.urlopen(request)
            output = open(PATH + save_to, 'wb')
            output.write(result.read())
            output.close()

        market['id'] = marketId
        market['urlExport'] = url
        market['last_update'] = datetime.datetime.now()
        market['dateCreate'] = datetime.datetime.now()
        for  event, elem in cElementTree.iterparse(PATH + save_to):
            if elem.tag == 'name':
                market['title'] = elem.text
                s = elem.text.replace(" ", "_")
                try:
                    market['transformedTitle'] = trans(s)[0]
                except:
                    market['transformedTitle'] = s
            if elem.tag == 'url':
                market['urlMarket'] = elem.text
            elem.clear()

        self.db.Market.insert(market)

        job = Download(url, marketId, save_to=save_to)
        job.run()
        return 'ok'

    def parse_by_id(self, id):

        """
            Функция для распарсивания файла выгрузки по идинтификатору
            магазина

            Получает:
                id - идинтификатор магазина

            Возвращает:
                eva - результат отработки парсера
        """

        market_result = self.db.Market.find_one({'id': int(id)})
        result = {}

        if market_result is None:
            result['message'] = "Market #%s was not found" % (id)
        else:
            url = market_result['urlExport']
            job = Download(url, id)
            self.db.Market.update({'id': id}, {"$set": {'state': job.eva}})

            try:
                job.run()
                job.eva['state'] = 'finished'
                self.db.Market.update({'id': id}, {
                    "$set": {'last_update': datetime.datetime.now(),
                             'state': job.eva}})
                result = job.eva

            except Exception as ex:
                print ex
                print job.eva['message']
                if job.eva['state'] == 'error':
                    self.db.Market.update({'id': id}, 
                                          {"$set": {'last_update': datetime.datetime.now(), 
                                                    'state': job.eva}})
                else:
                    job.eva['state'] = 'aborted'
                result = job.eva

            finally:
                if job.eva['added'] > 0:
                    self.db.Market.update({'id': id}, 
                                          {"$set": {'last_update': datetime.datetime.now(), 
                                                    'state': job.eva}})

        print "End Parsing: %s" % id
        return result

    def get_category(self, id):
        """
            Функция для получения категорий из магазина

            Получает:
                id - идинтификатор магазина

            Возвращает:
                eva - результат отработки парсера
        """

        job = Download(url, id)
        job.run()
        return job.eva

    def main(self):
        import time

        time_start = time.time()

        args = sys.argv[1:]
        action = args[0] if len(args) >= 1 else "help"
        id = int(args[1] if len(args) == 2 else 0)
        excluded_fields = {'Categories': 0, '_id': 0, 'dateCreate': 0,
                           'last_update': 0, 'lot_add': 0, 'lot_delete':0}

        print "[TASK] %s(%s):" % (action, id)

        if action == "help":
            print "=== HELP ==="
            print '''
    Usage: parse [list x] | [run x]
        list - list markets ids, x - page
        show - show market by id, x - market_id
        test - test YML by url from market, x - market_id
        run  - parse market by id, x - market_id
        reset - reset all states
            '''
        if action == "reset":
            print "=== RESETTING ALL MARKETS STATES ==="
            markets = self.db.Market.find({}, excluded_fields)
            for market in markets:
                print "Cleared for #%s - %s" % (market['id'], market['title'])
                self.db.Market.update({'id':market['id']}, {"$set": {'state': ''}})
        if action == "show":
            print "=== DETAILS MARKET #%s ===" % (id)
            market = self.db.Market.find_one({'id': id}, excluded_fields)
            if market is None:
                print "No market #%s found to show results" % (id)
            else:
                result = json.dumps(market, indent=4)
                print result.decode('raw_unicode_escape')
        if action == "list":
            print "=== LISTING MARKETS (records: %s-%s) ===" % (
            id * 10, id * 10 + 10)
            results = self.db.Market.find({}, excluded_fields).sort('id',
                                                                    1).skip(
                id * 10).limit(10)
            for market in results:
                title = '--NONAME--'
                if 'title' in market:
                    title = market['title']

                print "%s: %s" % (market['id'], title)
        elif action == "run":
            print "=== PARSING MARKET #%s ===" % (id)
            if id > 0:
                Parser().parse_by_id(id)
        elif action == "test":
            if id > 0:
                market = self.db.Market.find_one({'id': id}, {'urlExport': 1})
                if market is None:
                    print "No market #%s found to test by url" % (id)
                else:
                    print 'Testing YML: %s' % (market['urlExport'])
                    result = Parser().test(market['urlExport'])
                    print '     Result: %s' % (result)
        time_end = time.time()
        total_time = int(time_end - time_start)
        print " Total time: %s sec" % (total_time)

if __name__ == "__main__":
    Parser().main()
