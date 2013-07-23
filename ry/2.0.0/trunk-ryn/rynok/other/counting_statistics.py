# coding: utf-8
"""
Подсчет статистики
"""
import pymongo
import time
CONNECT_TO_STAT = 'rynok.yt:27020'
CONNECT_TO_RYNOK = ['10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019']
if __name__ == '__main__':
    DB = pymongo.Connection(CONNECT_TO_STAT).stat
    DBR = pymongo.Connection(CONNECT_TO_RYNOK).rynok
    LOT = DBR.Products
    Clicks = DB.Clicks
    View = DB.View
    TIME_START = time.time()
    TOTAL_TIME = 0
    COUNT = 0
    print "Start counting LOTS"
    for x in Clicks.find():
        LOT.update({'LotID':x['LotID']},{'$inc':{'Weight':1}})
        print x['LotID']
        COUNT += 1
        TOTAL_TIME += COUNT
    for x in View.find():
        LOT.update({'LotID':x['LotID']},{'$inc':{'Weight':0.1}})
        print x['LotID']
        COUNT += 1
        TOTAL_TIME += COUNT
    print "End import"
    TIME_END = time.time()
    print "Time: %s\nCount: %s\nCount per time: %s" % \
    (TIME_END - TIME_START, TOTAL_TIME, (TIME_END - TIME_START) / TOTAL_TIME)

