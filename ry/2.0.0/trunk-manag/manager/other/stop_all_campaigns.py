#!/usr/bin/python
from pymongo import Connection
rynok = Connection('10.0.0.8:27019').rynok

rynok.Products.remove()

for vendor in rynok.Vendors.find():
    vendor['count'] = 0
    rynok.Vendors.save(vendor)

for market in rynok.Market.find():
    market['count'] = 0
    rynok.Market.save(market)

for category in rynok.Category.find():
    category['count'] = 0
    rynok.Category.save(category)

for advertise in rynok.Advertise.find():
    advertise['state'] = {'status':'stopped', 'message':'Campaign stopped', 'started':None, 'finished':None}
#    advertise['state'] = False
    rynok.Advertise.save(advertise)
