# coding: utf-8
"""
Импорт товаров с базы парсера
"""
import pymongo
import time
import pyodbc
from trans import trans
import optparse
COUNT_TO_LOAD = 100000
CONNECT_TO_MONGO = '127.0.0.1:27017'#['10.0.0.8:27018, 10.0.0.8:27017, 10.0.0.8:27019']
CONNECT_TO_PARSER = '127.0.0.1:27017'
START_ID = 0
END_ID = 100000000
LAST_ID = START_ID
from datetime import datetime as dt
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-s", "--start-id", dest='START_ID', metavar="START_ID",
                      help=u"Начальный ID товара в база рынка")
    (options, args) = parser.parse_args()

    try:
        START_ID = int(options.START_ID)
    except:
        pass
    DB = pymongo.Connection(CONNECT_TO_MONGO).rynok
    MARKET = {}
    PARSER_DB = pymongo.Connections(CONNECT_TO_PARSER).parser
    DATA = PARSER_DB.Lot.find()

    for X in DATA:
        if not DB.Products.find_one({'LotID':X.LotID_int}) is None:
            continue
        try:
#                if COUNT >= COUNT_TO_LOAD:
#                    break;
            CATEG = 1
            ITEM = {}
            ITEM['Title'] = X.Title.decode('cp1251')
            try:
                t = unicode(ITEM['Title'])
            except:
                t = ITEM['Title']
                print t
            t = '_'.join(t.split())
            ITEM['Translited'] = trans(t)[0].strip().replace("(", " ").replace(")", " ").replace(" ", "_").replace("-", "_").replace(",", "").replace(".", "")
            ITEM['LotID'] = X.LotID_int
            MarketID = X.MarketID_int
            ITEM['ShopID'] = MarketID
            ITEM['ShopName'] = MARKET[MarketID]['Title']
            ITEM['ShopTransName'] = trans(MARKET[MarketID]['Translited'])[0].strip().replace("(", " ").replace(")", " ").replace(" ", "_").replace("-", "_").replace(",", "").replace(".", "")
            ITEM['AdCampaignID'] = X.SellerID_int
            ITEM['URLconf'] = 2
            ITEM['CategorID'] = CATEG.CategoryID
            ITEM['Weight'] = 0
            ITEM['StartDate'] = dt.now()
            ITEM['Descr'] = X.Description.decode('cp1251')
            ITEM['Price'] = X.Price.decode('cp1251')
            ITEM['PriceHistory'] = [{'date':dt.now()}, {'price':X.Price.decode('cp1251')}]
            ITEM['Currency'] = 'UHR'
            ITEM['CurrencyArray'] = [{'usd':'8.93'}, {'EUR':'CBRF'}]
            ITEM['Vendor'] = ''
            ITEM['VendorCode'] = ''
            ITEM['Param'] = []
            ITEM['URL'] = X.UrlToMarket.decode('cp1251')
            ITEM['Date'] = X.DateAdvert
            ITEM['ClickCost'] = X.ClickCost
            ITEM['ImageURL'] = "http://rynok.yottos.ru/img/" + X.ImageFilename.decode('cp1251')
            print "Count: %s, ID: %s" % (COUNT, ITEM['LotID'])
            #DB.Products.insert(ITEM)
            DB.Products.update({"LotID":ITEM['LotID']}, {"$set":ITEM}, upsert=True)
            LAST_ID = ITEM['LotID']
            COUNT += 1
        except Exception, ex:
            print "ID: %s Error on %s" % (ITEM['LotID'], ex)
#    except Exception, ex:
#        execfile("import_data.py", "START_ID=%s"%LAST_ID)
    print "End import"
    TIME_END = time.time()
    print "Time: %s\nCount: %s\nCount per time: %s" % \
    (TIME_END - TIME_START, COUNT, (TIME_END - TIME_START) / COUNT)

