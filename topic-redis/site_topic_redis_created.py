#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import redis
from pymongo import Connection, DESCENDING

redHost = 'srv-4.yottos.com'
monHost = '213.186.119.106:27017,213.186.121.201:27018,213.186.121.84:27018'
redCon = redis.Redis(host=redHost, port=6383, db=0)
monCon = Connection(host=monHost)
mDb = monCon.getmyad_db

def site_topic_created_to_redis():
    global mDb
    global redCon

    cursor = mDb.topic.url.find()
    redCon.flushall()
    for url in cursor:
        key = url.get('url', None)
        topics = url.get('topicIds', '')
        for topic in topics:
            redCon.sadd( key, topic)

if __name__ == '__main__':
    site_topic_created_to_redis()
    print redCon.keys()
