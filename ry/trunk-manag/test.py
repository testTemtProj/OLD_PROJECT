# coding: utf-8
from fabric.api import *
from pymongo import Connection

CONNECT_TO_MONGO = ['10.0.0.8:27017', '10.0.0.8:27018', '10.0.0.8:27019']

def test():
    db_parser = Connection(CONNECT_TO_MONGO)['parser']
    markets = db_parser.Market.find({},{'id':1, 'state':1, 'status_id':1})
    for market in markets:
        print market

test()