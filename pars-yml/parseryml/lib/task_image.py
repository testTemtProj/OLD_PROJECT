# coding: utf-8
import celery
from celery.task import task
from celery.task.sets import subtask, TaskSet
from downloadimage import download_once
import pymongo
import os
import urllib
import pymongo
import random
from ftplib import FTP
import StringIO
try:
    from PIL import Image
except ImportError:
    import Image
import uuid
import sys
from time import time, sleep
import urllib
import ConfigParser

import functools

from celery.events.state import state
import ftplib


PYLONS_CONFIG = "development.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config_images = ConfigParser.ConfigParser()
config_images.read(config_file)
 
PATH = "YML/"
PATH_TO_IMAGES = "IMG/"
PATH_TO_OUT_IMAGES = "IMG/OUT/"

#TODO: Переписать эту хуиту!!!
FOLDERS = ((213, 168), (128, 80), (98, 83))
WIDTH = 0
HEIGHT = 1
con = pymongo.Connection(config_images.get("app:main", 'mongo_host'))
db = con[config_images.get('app:main', 'mongo_database')]


def with_reconnect(func):
    '''
    Для реконекта к фтп серверу
    '''
    @functools.wraps(func)
    def _reconnector(*args, **kwargs):        
        for x in xrange(0, 20):
            try:                
                return func(*args, **kwargs)
            except:
                sleep(10)
        raise
    return _reconnector

       
@task()#max_retries=3, default_retry_delay=3 * 60)
def download_image(image, **kwargs):    
    try: 
        url = image['url']
        id = image['offer_hash']
        path = image['path']
        print "download image: %s" % url
        if download_once(url, id, path):
            return {'key':{'offer_hash':image['offer_hash']}, 'ok':True, 'url': path+'/'+id+'.jpg'}
        else:
            return {'ok':False}
    except Exception, ex:        
        print ex
        return {'ok':False}
        
    
@subtask
def download_picture(picture_url, picture_id):
    """Подзадача(subtask)
    Загрузка картинки и сохранение ее на диск
    Входные параметры:
    url - ссылка на изображение
    имя файла(свормированный из ид товарного предложения)
    """
    save_image = str(picture_id) + '.jpg'
    path = PATH_TO_IMAGES + str(save_image)[-7:-4] + '/'
    if not os.path.isdir(path):
        os.mkdir(path)
    img = urllib.urlopen(picture_url).read()
    f = file(path + save_image, "wb+")
    if f:
        f.write(img)
        f.close()
    
@subtask
def resize_picture(picture_id):
    """"Подзадача(subtask)
    Пержатия изображение
    Входной параметр:
    имя файла(свормированный из ид товарного предложения)
    """    
    result = []
    for p in FOLDERS:
        pp = str(picture_id)[-7:-4]
        path = PATH_TO_IMAGES + pp + '/'
        img = Image.open(path + picture_id)
        path = PATH_TO_OUT_IMAGES + p.keys()[0] + '/' + pp + '/'
        if not os.path.isdir(path):
            os.mkdir(path)
        img.thumbnail((p[WIDTH], p[HEIGHT]), Image.ANTIALIAS)
        if img.mode not in ('L', 'RGB'):
            img = img.convert("RGB")
        img.save(path + picture_id, "JPEG")

@subtask
def upload_and_remove(pictures):    
    ftp = FTP(host=config_images.get('app:main', 'ftp_host'),
              user=config_images.get('app:main', 'ftp_user'),
              passwd=config_images.get('app:main', 'ftp_pass'))
    ftp.cwd("images")                   
    for picture_id, picture_url in pictures.iteritems():
        
        for path in FOLDERS:
            pass
    ftp.quit()            

@task
def proccesing_pictrures(shop_id, **kwargs):
    """
    Задача обработки картинок изображения
    """
    picture_urls = {}
    tasks_image = []
    for pict_url in db.Offers.find(spec={'shopId':shop_id}, fields=['id', 'picture'], slave_ok=True):
        picture_urls[pict_url['id']] = pict_url['picture']
        tasks_image = (download_image.subtask(url=pict_url['picture'], id=pict_url['id']))
    job = TaskSet(tasks=tasks_image)
    result = job.apply_async()#connection, connect_timeout, publisher, taskset_id)
    result.wait()
    result.join()
    
    

