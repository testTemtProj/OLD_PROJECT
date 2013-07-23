#!/usr/bin/python
import httpagentparser
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import GeoIP
import urlparse


main_db_host = '213.186.119.106:27017,213.186.121.201:27018,213.186.121.84:27018'
conn = Connection(host=main_db_host)
db = conn.getmyad_db

gorg = GeoIP.open("GeoIPOrg.dat",GeoIP.GEOIP_STANDARD)
gisp = GeoIP.open("GeoIPISP.dat",GeoIP.GEOIP_STANDARD)


def normalizator(value):
    value = str(value).strip().upper()
    return value 
def normalizator_date(dt):
    if int(dt.strftime('%H')) < 5:
        value = 'NIGHT'
    elif int(dt.strftime('%H')) < 9:
        value = 'MORNING'
    elif int(dt.strftime('%H')) < 15:
        value = 'DAYTIME'
    elif int(dt.strftime('%H')) < 21:
        value = 'EVENING'
    else:
        value = 'NIGHT'
    return value

def normarizator_referer(url):
    search = ['google', 'yandex', 'rambler', 'rapidall', 'nigma', 'msn', 'ask', 'qip', 'live']
    if urlparse.parse_qs(url).get('referrer', None) == None:
        ref = 'NONE_REF'
    elif urlparse.urlparse(urlparse.parse_qs(url).get('referrer', ('',))[0]).netloc.endswith(urlparse.urlparse(urlparse.parse_qs(url).get('location', ('',))[0]).netloc.replace('www.', '')):
        ref = 'SERF'
    elif True in [item in search for item in urlparse.urlparse(urlparse.parse_qs(url).get('referrer', ('',))[0]).netloc.split('.')]:
        ref = 'SERCH'
    else:
        ref = 'OTHER'
    return ref



def mongo_clicks(db):
    date = datetime.datetime(2012, 07, 16)
    clicks = db.clicks.find({'dt': {'$gte': date}})
    for c in clicks:
        os = normalizator(httpagentparser.detect(c['user_agent']).get('os', {}).get('name', 'None'))
        os_ver = normalizator(httpagentparser.detect(c['user_agent']).get('os', {}).get('version', 'None'))
        os_dist = normalizator(httpagentparser.detect(c['user_agent']).get('dist', {}).get('name', 'None'))
        os_dist_ver = normalizator(httpagentparser.detect(c['user_agent']).get('dist', {}).get('version', 'None'))
        user_agent = normalizator(httpagentparser.detect(c['user_agent']).get('browser', {}).get('name', 'None'))
        user_agent_ver = normalizator(httpagentparser.detect(c['user_agent']).get('browser', {}).get('version', 'None'))
        isp =  normalizator(gisp.org_by_name(c['ip']) if gisp.org_by_name(c['ip']) != None else 'None')
        org = normalizator(gorg.org_by_name(c['ip']) if gorg.org_by_name(c['ip']) != None else 'None')
        city = normalizator(c['city'])
        country = normalizator(c['country'])
        inf =  normalizator(c['inf'])
        dt = normalizator_date(c['dt'])
        ref = normarizator_referer(c['referer'])
        #print os, '\t', os_ver, '\t', os_dist, '\t', os_dist_ver, '\t', user_agent, '\t', user_agent_ver, '\t', isp, '\t', org, '\t', city, '\t', country, '\t', ref, '\t', dt, '\t', inf
        print '"'+os+'","'+os_ver+'","'+os_dist+'","'+os_dist_ver+'","'+user_agent+'","'+user_agent_ver+'","'+isp+'","'+org+'","'+city+'","'+country+'","'+ref+'","'+dt+'"', inf
        break


if __name__ == '__main__':
    mongo_clicks(db)
