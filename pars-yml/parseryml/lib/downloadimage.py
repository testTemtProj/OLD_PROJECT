# coding: utf-8
import os
import urllib
#import pymongo
#from pymongo import Connection
from ftplib import FTP
try:
    from PIL import Image
except ImportError:
    import Image

try:
    from eventlet.green import urllib2
except ImportError:
    import urllib as urllib2
#from pylons import app_globals
import functools
from time import sleep
import ConfigParser
PYLONS_CONFIG = "development.ini"
config_file = '%s/../../%s' % (os.path.dirname(__file__), PYLONS_CONFIG)
config_images = ConfigParser.ConfigParser()
config_images.read(config_file)

COUNT = 0

PATH_TO_IMAGES = '%s/../../%s' % (os.path.dirname(__file__), config_images.get('app:main', 'path_to_images'))
PATH_TO_OUT_IMAGES = '%s/../../%s' % (os.path.dirname(__file__), config_images.get('app:main', 'path_to_out_images'))


FOLDERS = [
#           {"213x168":(213, 168)},
#           {"120x120":(120, 120)},
           {"100x110":(100, 110)},
           ]
SIZES = ((213, 168), (128, 80), (98, 83))
width = 0
height = 1


def with_retry(func):
    '''
    Для реконекта к фтп серверу
    '''
    @functools.wraps(func)
    def _retry(*args, **kwargs):        
        for x in xrange(0, 3):
            try:                
                return func(*args, **kwargs)
            except:# ftplib.all_errors:
                sleep(10)
        raise
    return _retry

class AppURLopener(urllib.FancyURLopener):
    version = "YottosImageParser/0.3 (http://rynok.yottos.com)"

urllib._urlopener = AppURLopener()

class DownloadJobImage():
    """
    Класс загрузки и пережатия картинки
    """
    def __init__(self, url, id, path=None):
        self.url = url
        self.id = id        
        self.path = PATH_TO_IMAGES + path + "/"
        
#    @with_retry    
    def download(self, url, id):
        """Загрузка изображения"""
        save_image = str(id) + '.jpg'
        #path = PATH_TO_IMAGES + id[-3:] + '/'                
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
            #os.mkdir(path)
        img = urllib2.urlopen(url)
        mime = img.info().gettype()
        if mime.find('image')<0:
            return None
        img = img.read()
        f = file(self.path + save_image, "wb+")
        
        if f:
            f.write(img)            
            f.close()
        else:
            print "Error save file"
            return None
        return save_image

    def resize(self, filename):
        """Пережатие изображения"""
        result = []
        for p in FOLDERS:            
            pp = str(filename)[-7:-4]            
            path = self.path                                    
            img = Image.open(path + filename)            
            new_path = path.replace('orig', p.keys()[0])
            if not os.path.isdir(new_path):
                os.makedirs(new_path)
            img.thumbnail((p.values()[0][width], p.values()[0][height]), Image.ANTIALIAS)
            if img.mode not in ('L', 'RGB'):
                img = img.convert("RGB")
            
            img.save(new_path + filename, "JPEG")            
            result.append([p.keys()[0], path, filename, pp])   
        return result
         
    @with_retry
    def upload(self, path, filename):
        """Заливка изображения на фтп"""
        if self.ftp is None:
            return
                
        ftp = self.ftp()                            
        f = file(filename[0]+filename[1], 'rb+')
        image_file = f        
        ftp.cwd("/var/www/cdnt.yt/images")                   
        ftp.cwd(path)      
            
        try:                                                                
            ftp.cwd(filename[2])
        except:
            ftp.mkd(filename[2])
            ftp.cwd(filename[2])
                        
        ftp.storbinary('STOR %s' % filename[1], image_file)
        if f:
            f.close()
        
        try:
            if f.closed:
                pass#os.remove(filename[0]+filename[1])
        except Exception, ex:            
            print ex
            
        return filename
    
     
    def run(self):
            f = self.download(url=self.url, id=self.id)
            if f is None:
                return None
            self.resize(f)
            path = self.id[-3:]+'/'+self.id+".jpg"                

            return path



def download_once(url, id, path):
    """
    Загрузка одной картинки
    """   
    try: 
        job = DownloadJobImage(url, id, path)
        return job.run()
    except:
        return False
    
    

if __name__ == "__main__":
    download_once("http://www.mobilluck.com.ua/pics/photo/mobila/lg/LG_GW_620_11145_10991.jpg", id="11145104061618")
    exit(0)
