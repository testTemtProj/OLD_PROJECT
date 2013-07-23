#from catalog.model.modelBase import Base
from celery.task import task
from httplib import HTTP
from urlparse import urlparse
import pymongo
import datetime

@task
def test():
    print 'running task'
    

@task
def check_url(site_id):
    con = pymongo.Connection(['10.0.0.8:27017','10.0.0.8:27018','10.0.0.8:27019'])#Base.site_collection
    url = con.find_one({"id":site_id})['reference']
    path = urlparse(url)
    header = HTTP(path[1])
    try:
        header.putrequest('HEAD', path[2])
        header.endheaders()
    except:
        con.update({"id":site_id},{"$set":{"avaible":False}})
        return 0
    else:
        con.update({"id":site_id},{"$set":{"avaible":True}})
        con.update({"id":site_id},{"$set":{"last_checked":datetime.datetime(datetime.date.today().year,datetime.date.today().month,datetime.date.today().day)}})
        if header.getreply()[0] == 200: con.update({"id":site_id},{"$set":{"avaible":True}});return 1
        else: con.update({"id":site_id},{"$set":{"avaible":False}})
        return 0 
        
