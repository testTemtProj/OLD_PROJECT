#!/usr/bin/python
# encoding: utf-8
from ftplib import FTP
import pymongo
import StringIO
import re
from sys import argv


def _generate_informer_loader(informer_id):
    ''' Возвращает код javascript-загрузчика информера '''
    global adshow_url
    db = pymongo.Connection(host='yottos.com').getmyad_db
    adv = db.informer.find_one({'guid': informer_id.lower()})
    if not adv:
        return False
    try:
        guid = adv['guid']
        width = int(re.match('[0-9]+',
                    adv['admaker']['Main']['width']).group(0))
        height = int(re.match('[0-9]+',
                    adv['admaker']['Main']['height']).group(0))
    except:
        raise Exception("Incorrect size dimensions for informer %s" % informer_id)
    try:
        border = int(re.match('[0-9]+',
                    adv['admaker']['Main']['borderWidth']).group(0))
    except:
        border = 1
    partner = adv.get('domain', 'other').replace('.', '_').replace('/', '')
    width += border * 2
    height += border * 2
    return (""";function windowWidth(){var a=document.documentElement;return self.innerWidth||a&&a.clientWidth||document.body.clientWidth}"""
            """;function windowHeight(){var a=document.documentElement;return self.innerHeight||a&&a.clientHeight||document.body.clientHeight}"""
            """;document.write("<iframe src='http://%s.%s?scr=%s&location=" + """
            """encodeURIComponent(window.location.href) + "&referrer=" + encodeURIComponent(document.referrer) + """
            """ "&w=" + windowWidth() + "&h=" + windowHeight() + """
            """ "&rand=" + Math.floor(Math.random() * 1000000) + "' width='%s' height='%s'  frameborder='0' scrolling='no'></iframe>");"""
            ) % (partner, adshow_url, guid, width, height)



def upload_all():
    # Параметры FTP для заливки загрузчиков информеров
    informer_loader_ftp = '213.186.121.86'
    informer_loader_ftp_user = 'cdn'
    informer_loader_ftp_password = '$www-app$'
    informer_loader_ftp_path = 'httpdocs/getmyad'
    db = pymongo.Connection(host='yottos.com').getmyad_db

    ftp = FTP(host=informer_loader_ftp,
              user=informer_loader_ftp_user,
              passwd=informer_loader_ftp_password)
    ftp.cwd(informer_loader_ftp_path)
    
    informers = [x['guid'] for x in db.informer.find({}, ['guid'])]
    informers += map(lambda x: x.upper(), informers)        # Для тех, кому выдавался upper-case GUID
    
    for informer in informers:
        print "Uploading %s" % informer
        loader = StringIO.StringIO()
        loader.write(_generate_informer_loader(informer))
        loader.seek(0)
        ftp.storlines('STOR %s.js' % informer, loader)
    #informer = '3bfe6280-1b8f-11e1-ae13-00163e0300c1'
    #loader = StringIO.StringIO()
    #loader.write(_generate_informer_loader(informer))
    #loader.seek(0)
    #ftp.storlines('STOR %s.js' % informer, loader)

    
    ftp.quit()
    loader.close()
    
def usage():
    print "Направление трафика GetMyAd на сервера Yottos."
    print "Использование: generate-loaders rg"
    print ""
    print "Параметры:"
#    print "    balancer33  балансировщик на vsrv-3.3"
#    print "    balancer32  балансировщик на vsrv-3.2"
#    print "    vsrv12      напрямую на vsrv-1.2"
#    print "    vsrv13      напрямую на vsrv-1.3"
    print "    rg          на rg.yottos.com"
    exit()


if __name__ == '__main__':
    if len(argv) <> 2:
        usage()
        
    if argv[1] == 'rg':
        adshow_url = 'rg.yottos.com/adshow.fcgi'
    else:
        usage() 

    upload_all()
    print "Finished!"
    
