# -*- coding: utf-8 -*-
# Выводит статистику переходов GetMyAd по странам
import pygeoip
from datetime import datetime
from pymongo import Connection

conn = Connection()
db = conn.getmyad_db
gi = pygeoip.GeoIP('c:/data/GeoIP.dat')

stat = {}
for x in db.log_clicks.find({'unique': True}):
    country = gi.country_code_by_addr(x['ip'])
    adv = x['adv']
    if not stat.has_key(adv):
        stat[adv] = {}
    if country in stat[adv]:
        stat[adv][country] += 1
    else:
        stat[adv][country] = 1


totalNonUa = 0

for adv, s in stat.items():
    advertise = db.Advertise.find_one({'guid': adv})['title']
    print advertise
    print '=================================='
    s = s.items()
    s.sort(key=lambda x: x[1], reverse=True)
    ua = sum([x[1] for x in s if x[0]=='UA'])
    non_ua = sum([x[1] for x in s if x[0]<>'UA'])
    totalNonUa += non_ua 
    
    print '\n'.join(['%s\t%s' % (x[0], x[1]) for x in s])
    print '----------------------------------'
    print 'Ukraine:', ua
    print 'Non-Ukraine:', non_ua
    print 'Non-Ukraine ratio: %.0f%%' % (non_ua * 100.0 / (ua+non_ua))
    print '\n'
    
    
print "TOTAL NONUA", totalNonUa