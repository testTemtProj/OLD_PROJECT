import pymongo
from celery.task import task,sets
from tasks import check_url
from catalog.model.modelBase import Base
#connection = pymongo.Connection()
collection = pymongo.Connection(['10.0.0.8:27017','10.0.0.8:27018','10.0.0.8:27019']).catalog.site

sites = collection.find({},{'id':1})#.limit(10)

@task
def check_sites():
    task_set = sets.TaskSet(check_url.subtask((site['id'], )) for site in sites)
    result = task_set.apply()

