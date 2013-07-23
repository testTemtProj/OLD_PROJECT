#!/usr/bin/python
import httpagentparser
from pymongo import Connection, DESCENDING
import datetime
import pymongo
from pysqlite2 import dbapi2 as sqlite
import GeoIP
from pprint import pprint
import urlparse
import nn

mynet=nn.searchnet('nn.db')

main_db_host = '213.186.119.106:27017,213.186.121.201:27018,213.186.121.84:27018'
conn = Connection(host=main_db_host)
db = conn.getmyad_db

con = sqlite.connect('key.db')
cur = con.cursor()

gorg = GeoIP.open("GeoIPOrg.dat",GeoIP.GEOIP_STANDARD)
gisp = GeoIP.open("GeoIPISP.dat",GeoIP.GEOIP_STANDARD)

def normalizator(table, column, value):
    try:
        ssql = '''select * from %s where %s = "%s"''' % (table, column, str(value).strip().upper())
        isql = '''insert into %s(%s) values ("%s")'''  % (table, column, str(value).strip().upper())
        if cur.execute(ssql).fetchone() == None:
            cur.execute(isql)
            con.commit()
            integer = cur.execute(ssql).fetchone()[0]
        else:
            integer = cur.execute(ssql).fetchone()[0]
    except:
        integer = 10000
    return int(integer) 

def normalizator_date(dt):
    if int(dt.strftime('%H')) < 5:
        integer = 4
    elif int(dt.strftime('%H')) < 9:
        integer = 1
    elif int(dt.strftime('%H')) < 15:
        integer = 2
    elif int(dt.strftime('%H')) < 21:
        integer = 3
    else:
        integer = 4 
    return int(integer)

def normarizator_referer(url):
    search = ['google', 'yandex', 'rambler', 'rapidall', 'nigma', 'msn', 'ask', 'qip', 'live']
    if urlparse.parse_qs(url).get('referrer', None) == None:
        ref = 1
    elif urlparse.urlparse(urlparse.parse_qs(url).get('referrer', ('',))[0]).netloc.endswith(urlparse.urlparse(urlparse.parse_qs(url).get('location', ('',))[0]).netloc.replace('www.', '')):
        ref = 2
    elif True in [item in search for item in urlparse.urlparse(urlparse.parse_qs(url).get('referrer', ('',))[0]).netloc.split('.')]:
        ref = 3
    else:
        ref = 4
    return ref



def mongo_clicks(db):
    AllGroup=[1, 2, 3, 4]
    date = datetime.datetime(2012, 07, 06)
    clicks = db.clicks.find({'dt': {'$gte': date}})
    print datetime.datetime.now()
    for c in clicks:
        os = normalizator('user_os', 'name', httpagentparser.detect(c['user_agent']).get('os', {}).get('name', 'None'))
        os += 10000
        os_ver = normalizator('user_os_ver', 'ver', httpagentparser.detect(c['user_agent']).get('os', {}).get('version', 'None'))
        os_ver += 20000
        os_dist = normalizator('os_dist', 'name', httpagentparser.detect(c['user_agent']).get('dist', {}).get('name', 'None'))
        os_dist += 30000
        os_dist_ver = normalizator('os_dist_ver', 'ver', httpagentparser.detect(c['user_agent']).get('dist', {}).get('version', 'None'))
        os_dist_ver += 40000
        user_agent = normalizator('user_agent_name', 'name', httpagentparser.detect(c['user_agent']).get('browser', {}).get('name', 'None'))
        user_agent += 50000
        user_agent_ver = normalizator('user_agent_ver', 'ver', httpagentparser.detect(c['user_agent']).get('browser', {}).get('version', 'None'))
        user_agent_ver += 60000
        isp =  normalizator('isp', 'name', gisp.org_by_name(c['ip']) if gisp.org_by_name(c['ip']) != None else 'None')
        isp += 70000
        org = normalizator('org', 'name', gorg.org_by_name(c['ip']) if gorg.org_by_name(c['ip']) != None else 'None')
        org += 80000 
        city = normalizator('city', 'name', c['city'])
        city += 90000
        country = normalizator('country', 'name', c['country'])
        country += 10000
        inf =  normalizator('informer', 'name', c['inf'])
        inf += 11000
        dt = normalizator_date(c['dt'])
        ref = normarizator_referer(c['referer'])
        ref += 12000
        print os, os_ver, os_dist, os_dist_ver, user_agent, user_agent_ver, isp, org, city, country, inf, ref, dt
        print datetime.datetime.now()
        mynet.trainquery([os, os_ver, os_dist, os_dist_ver, user_agent, user_agent_ver, isp, org, city, country, inf, ref], AllGroup, dt)
        print datetime.datetime.now()
        #print inf, org, country, dt
        #mynet.trainquery([inf, org, country], AllGroup, dt)
        #break
    print datetime.datetime.now()


if __name__ == '__main__':
    mongo_clicks(db)
