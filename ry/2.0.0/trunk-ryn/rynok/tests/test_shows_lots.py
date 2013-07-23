# coding: utf-8
"""
Приблизительный тест на нагрузку
"""
from random import choice, randint, random
from time import time
from urllib import urlopen
from datetime import datetime as dt
import pymongo
PAGE_COUNT = 10000
URL = "http://10.0.0.132:5000/product/show?id="
ID = []
if __name__ == '__main__':
    db = pymongo.Connection(['10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019']).rynok.Products
    for x in db.find().limit(1000):
        ID.append(str(x['LotID']))
    d1 = dt.now()
    t1 = time()
    total_size = 0
    print "%s: Start download %s pages" % (d1, PAGE_COUNT)
    count = 0
    fail = 0
    while count < PAGE_COUNT:
        url = URL + ID[randint(0, 999)]
        tt = time()
        try:
            page = urlopen(url)
            size = len(page.read())
            total_size += size
            print "%s) %s: size: %sKb in %s Sec" % (count, url, size / 1024, time() - tt)
        except:
            print "%s) %s: Fail in %s Sec" % (count, time() - tt)
            fail += 1
        count += 1
    print "End \nFails: %s\nTotal size: %sKb\nTotal time: %s" % (fail, total_size / 1024, time() - t1)
