# -*- coding: utf-8 -*-
import logging
import re
import string
import json
import datetime
import time
from pylons import request, response, session, tmpl_context as c, url, app_globals
from pylons.controllers.util import abort, redirect
from pymongo import Connection
from getmyad.lib.base import BaseController, render
import base64
log = logging.getLogger(__name__)

class StatController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/hello.mako')
        # or, Return a response
        
        return render("/stat.mako.html") 
    
    
    def get_data(self):
        #Возвращаем данные для таблицы
        #db = Connection("yottos.com").stat
        db = Connection("213.186.121.201").stat
        #db = app_globals.db.stat
        domain = str(request.params['site']).replace("'", "")
        start_date = request.params['start_date']
        end_date = request.params['end_date']
         
        d1 = datetime.datetime(*time.strptime(start_date, "%d.%m.%Y")[0:5])
        d2 = datetime.datetime(*time.strptime(end_date, "%d.%m.%Y")[0:5])          
        ref_per_domain = {}
        result = []
        refs = []
        reffers = []
        log.info(d1)
        #return str(d1)→   
        #return db.Result.find({'user':domain, "date" : {"$gte":d1, "$lte":d2}})
        count = 0
        log.info("Query to Db")
        domain_per_reffer = {}
        print domain
        for ref in db.stat_per_date.find({'domain': domain, "date" : {"$gte":d1, "$lte":d2}}):
            count += 1        
            key = (ref['referrer'], ref['from_getmyad'])
            value = domain_per_reffer.setdefault(key, {'3': 0,
                                       '15': 0,
                                       '30': 0,
                                       '60': 0})
            value['3'] += ref['duration']['3']
            value['15'] += ref['duration']['15']
            value['30'] += ref['duration']['30']
            value['60'] += ref['duration']['60']
            #try:
        getmyad = {'site':'http://getmyad.yottos.com',
                 'from_getmyad':False,
                 'time3': 0,
                 'time15': 0,
                 'time30':0,
                 'time60': 0}


        for x, val in domain_per_reffer.items():
            if x[1]:
                getmyad['time3'] += val['3']
                getmyad['time15'] += val['15']
                getmyad['time30'] += val['30']
                getmyad['time60'] += val['60']
            result.append({'site':x[0],
                           'time3':val['3'],
                           'time15':val['15'],
                           'time30':val['30'],
                           'time60':val['60'],
                           'from_getmyad':x[1]})

            #except Exception, ex:
            #   print ex
        result.append(getmyad)
        log.info(count)        
        return json.dumps(result)          
#            for x in db.Result.find({'user':domain, "date" : {"$gte":d1, "$lte":d2}}):
#                result.append(x)                
#            return json.dumps(db.Result.find({'user':domain, "date" : {"$gte":d1, "$lte":d2}}))
        #except Exception, e:
            #return e
    
        for x in app_globals.db.AllPartner.find():
            reffers.append(x['Domain'])
        for ref in reffers:
            ref_re = re.compile(ref, re.IGNORECASE)
            count_3 = 0
            count_15 = 0
            count_30 = 0
            count_60 = 0            
            for x in db.Result.find({"site":ref_re, "date" : {"$gte":d1, "$lte":d2}}):
                try:
                    #print "\n\nnode:%s\nref:%s\ndomain:%s \n\n"%(x,ref,domain)
                    #print x['path'][0]['url']
                    if string.index(x['path'][0]['url'], domain) > -1:                  
                        if x['duration'] < 15:
                            count_3 += 1
                        if 15 < x['duration'] < 30:
                            count_15 += 1
                        if 30 < x['duration'] < 60:
                            count_30 += 1
                        if 60 < x['duration']:
                            count_60 += 1                
                except:
                    continue
                ref_per_domain[ref] = [{"count": count_3},
                                    {"count": count_15},
                                    {"count": count_30},
                                    {"count": count_60}]
            #result.append({domain:ref_per_domain})
        for ref in ref_per_domain:
            result.append({'site':ref, 'time':ref_per_domain[ref]})
        return json.dumps(result)
#print result
        
        
    def domains(self):
        ###################
        #db = Connection('213.186.121.201').stat
        #db = Connection().stat
        db = Connection("213.186.121.201").stat
        #db = app_globals.db.stat
        domains = []
        log.info(db.Domain.count())
        for item in db.Domain.find():
            log.info(item)
            domains.append(item['url'])
            
        return json.dumps(domains)
    
        domain_re = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9-]+\.)+[A-Z]{2,6}|'
            r'localhost|'
            r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?',
            re.IGNORECASE)
        for rec in app_globals.db.ResultStat.find():
            str = rec['path'][0]['url']
            res = re.findall(domain_re, str)
            if len(res) > 0 and not string.lower(res[0]) in domains :
                domains.append(string.lower(res[0]))   
                #db.AllDomain.update({'Domain': res[0]}, {'$set': {'value': res[0]}}, upsert=True)          
        return json.dumps(domains)
    
