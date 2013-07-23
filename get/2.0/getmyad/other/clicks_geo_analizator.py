#!/usr/bin/python
from pymongo import Connection, DESCENDING
import datetime
import pymongo
import GeoIP
import subprocess
gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
gc = GeoIP.open("/usr/local/share/GeoIP/GeoLiteCity.dat",GeoIP.GEOIP_STANDARD)
main_db_host = '213.186.119.106:27017,213.186.121.201:27018,213.186.121.84:27018'
conn = Connection(host=main_db_host)
db = conn.getmyad_db

def geo_clicks(db):
    cursor = db['clicks'].find()
    ip_buffer = {}
    processed_records = 0
    for click in cursor:
        key = (click['ip'])
        ip_buffer[key] = ip_buffer.get(key, 0) + 1
        processed_records += 1
    geo_buffer = {}    
    for key,value in ip_buffer.items():
#        p = subprocess.Popen("/home/www-app/develop/tmp/get_ip/bin/get_ip %s" % key, shell=True,stdout=subprocess.PIPE)
#        out = p.stdout.read()
        country = gi.country_name_by_addr(key)
        if country == None:
            country = 'None'
        city = gc.record_by_addr(key)
        if city == None:
            city = 'None'
        else:
            city = city['city'] if 'city' in city and city['city'] != None else 'None'

        key = (country, city)
        geo_buffer[key] = geo_buffer.get(key, 0) + value

    for key,value in sorted(geo_buffer.items()):
        print ' '.join(key), (float(value)/float(processed_records))*100







if __name__ == '__main__':
    geo_clicks(db)
