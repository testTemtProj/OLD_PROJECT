# Encoding: utf-8
# Создаёт статические javascript показа информера для каждой выгрузки

from ftplib import FTP
from pymongo import Connection
from pylons import app_globals
import StringIO
import re

class progressBar:
    def __init__(self, minValue = 0, maxValue = 10, totalWidth=12):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = minValue
        self.max = maxValue
        self.span = maxValue - minValue
        self.width = totalWidth
        self.amount = 0       # When amount == max, we are 100% done 
        self.updateAmount(0)  # Build progress bar string

    def updateAmount(self, newAmount = 0):
        if newAmount < self.min: newAmount = self.min
        if newAmount > self.max: newAmount = self.max
        self.amount = newAmount

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.amount - self.min)
        percentDone = (diffFromMin / float(self.span)) * 100.0
        percentDone = round(percentDone)
        percentDone = int(percentDone)

        # Figure out how many hash bars the percentage should be
        allFull = self.width - 2
        numHashes = (percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # build a progress bar with hashes and spaces
        self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

        # figure out where to put the percentage, roughly centered
        percentPlace = (len(self.progBar) / 2) - len(str(percentDone)) 
        percentString = str(percentDone) + "%"

        # slice the percentage into the bar
        self.progBar = self.progBar[0:percentPlace] + percentString + self.progBar[percentPlace+len(percentString):]

    def __str__(self):
        return str(self.progBar)


class InformerUploader:
    def __init__(self):
        self.url = 'plesk2.dc.utel.ua'
        self.login = 'zcdnyott1709com'
        self.password = 'D%l)s2v6'
        self.ftp = None
        self.db = app_globals.db
        
        
    def __del__(self):
        self.disconnect()
        
    
    def connect(self):
        """ Подключается к FTP серверу """
        self.ftp = FTP(self.url)
        self.ftp.login(self.login, self.password)
        self.ftp.cwd('httpdocs')
        self.ftp.cwd('getmyad')
    
    
    def upload(self, informer_id):
        """ Загружает на FTP скрипт составления информера informer_id """
        if not self.ftp:
            self.connect()
        adv = self.db.Advertise.find_one({'guid': informer_id})
        if not adv:
            return False
        try:
            guid = adv['guid']
            width = int(re.match('[0-9]+', adv['admaker']['Main']['width']).group(0))
            height = int(re.match('[0-9]+', adv['admaker']['Main']['height']).group(0))
        except:
            raise Exception("Incorrect size dimensions for informer %s" % guid)
        try:
            border = int(re.match('[0-9]+', adv['admaker']['Main']['borderWidth']).group(0))
        except:
            border = 1
        width += border*2
        height += border*2 

        informer = StringIO.StringIO()
        informer.write(""";document.write("<iframe src='http://rynok.yottos.com.ua/p_export.aspx?scr=%s' width='%s' height='%s'  frameborder='0' scrolling='no'></iframe>");""" 
                       % (guid, width, height))
        informer.seek(0)
        self.ftp.storlines('STOR %s.js' % guid, informer)
        informer.close()
        
        
    def uploadAll(self):
        """ Загружает на FTP скрипты для всех информеров """
        advertises = self.db.Advertise.find({}, {'guid': 1})
        prog = progressBar(0, advertises.count())
        i = 0
        for adv in advertises:
            i+= 1
            prog.updateAmount(i)
            print "Saving informer %s... \t\t\t %s" % (adv['guid'], prog)
            
            self.upload(adv['guid'])

    
    def disconnect(self):
        """ Отключение от FTP-сервера """
        if self.ftp:
            self.ftp.quit()
