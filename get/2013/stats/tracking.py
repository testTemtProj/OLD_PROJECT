# encoding: utf-8
# This Python file uses the following encoding: utf-8
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import bson.objectid
import redis
from sphinxapi import *
from binascii import crc32
import urlparse

class GetmyadTracking():
    def _textClean(self, string):
        p = re.compile(u'[^а-яА-Яa-zA-Z]', re.UNICODE)
        string = p.sub(' ',string)
        p = re.compile(u'\s+', re.UNICODE)
        string = p.sub(' ',string)
        string = string.strip().encode('utf-8')
        return string
    def _queryConstryctor(self, string):
        string = self._textClean(string)
        q = ' | '.join(string.split(' ')).decode('utf-8')
        return q

    def trackingAnalytic(self, db, redisRetargeting):
        host = '127.0.0.1'
        port = 9312
        index = 'retargeting'
        Weights = {'url':99, 'domain':60, 'urlpatch':70, 'urlparam':50, 'title':10, 'description':10, 'keywords':15, 'exactly_phrases':25, 'phrases':20}
        mode = SPH_MATCH_EXTENDED2
        cl = SphinxClient()
        cl.SetServer ( host, port )
        cl.SetMatchMode ( mode )
        cl.SetFieldWeights ( Weights )
        cl.SetLimits(0,2)
        updateData = {} 
        cursor = db.tracking.stats_daily.find({ "change": True })
        for item in cursor:
            keyMap = str(item['cookie']) + '-' + str(item['ip'])
            for red in redisRetargeting:
                try:
                    con = redis.Redis(host = red[0], port = red[1], db = 0)
                    con.delete(keyMap)
                except Exception as e:
                    print e
            for key, value in item['remarketing_url'].iteritems():
                account = crc32(str(value[3])) & 0xffffffff
                cl.SetFilter( 'faccountid', [account,], 0 )
                url = value[0]
                search = value[1] if value[1] != None else None
                context = value[2] if value[2] != None else None
                url_list = list(urlparse.urlparse(url))
                q = '( '
                escapeQ = cl.EscapeString(url)
                q += ' (@url '+ escapeQ+') '
                escapeQ = cl.EscapeString(url_list[1])
                q += '| (@domain '+ escapeQ+') '
                if len(self._textClean(url_list[2])) > 0:
                    escapeQ = cl.EscapeString(url_list[2])
                    q += '| (@urlpatch '+ escapeQ+') '
                    q += '| (@urlpatch ' + self._queryConstryctor(url_list[2]) +') '
                if len(self._textClean(url_list[4])) > 0:
                    escapeQ = cl.EscapeString(url_list[4])
                    q += '| (@urlparam '+ escapeQ+') '
                    q += '| (@urlparam '+ self._queryConstryctor(url_list[4]) +') ' 
                if search != None:
                    query = self._queryConstryctor(search)
                    if len(query) > 0:
                        q += '| (@(title,description,keywords,exactly_phrases,phrases) ' + query +' ) '
                if context != None:
                    query = self._queryConstryctor(context)
                    if len(query) > 0:
                        q += '| (@(title,description,keywords,exactly_phrases,phrases) ' + query +' ) '
                q += ' )'
                cl.AddQuery(q, index )
                res = cl.RunQueries()
                match = False
                for sitem in res:
                    if sitem.has_key('matches'):
                        for match in sitem['matches']:
                            guid = None
                            guid = match.get('attrs',{'guid': None})['guid']
                            if guid != None:
                                match = True
                                updateData[keyMap] = updateData.get(keyMap,list()) + [guid]
                                for red in redisRetargeting:
                                    try:
                                        con = redis.Redis(host = red[0], port = red[1], db = 0)
                                        con.zadd(keyMap, guid, 1)
                                    except Exception as e:
                                        print e
                if not match:
                    mode = SPH_MATCH_ALL
                    cl.SetMatchMode ( mode )
                    cl.AddQuery('', index )
                    res = cl.RunQueries()
                    for sitem in res:
                        if sitem.has_key('matches'):
                            for match in sitem['matches']:
                                guid = None
                                guid = match.get('attrs',{'guid': None})['guid']
                                if guid != None:
                                    updateData[keyMap] = updateData.get(keyMap,list()) + [guid]
                                    for red in redisRetargeting:
                                        try:
                                            con = redis.Redis(host = red[0], port = red[1], db = 0)
                                            con.zadd(keyMap, guid, 1)
                                        except Exception as e:
                                            print e
                                    break
                    mode = SPH_MATCH_EXTENDED2
                    cl.SetMatchMode ( mode )
                cl.ResetFilters()
            offerList = list(set(updateData.get(keyMap, list())))
            if len(offerList) > 0:
                item['remarketing_offer'] = offerList
            item['change'] = False
            db.tracking.stats_daily.save(item)
