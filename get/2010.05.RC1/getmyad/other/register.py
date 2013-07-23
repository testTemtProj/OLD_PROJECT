# -*- coding: utf-8 -*-
import pyodbc
from pymongo import Connection
from random import Random
from datetime import datetime
import sys
from optparse import OptionParser
import uuid
import re


connection_string = 'DRIVER={SQL Server};server=WS1;DATABASE=1gb_YottosAdload;UID=sa;PWD=1'

#conn = pyodbc.connect('DRIVER={SQL Server};server=213.186.119.106;DATABASE=1gb_YottosAdload;UID=web;PWD=odif8duuisdofj', autocommit=True)
mongo_conn = Connection()
mongo_db = mongo_conn.getmyad_db


def makePassword():
    """Возвращает сгенерированный пароль"""
    rng = Random()

    righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
    lefthand = '789yuiophjknmYUIPHJKLNM'
    allchars = righthand + lefthand
    
    passwordLength = 8
    alternate_hands = True
    password = ''
    
    for i in range(passwordLength):
        if not alternate_hands:
            password += rng.choice(allchars)
        else:
            if i % 2:
                password += rng.choice(lefthand)
            else:
                password += rng.choice(righthand)
    return password



def createUser(login):
    """Создаёт пользователя GetMyAd"""
    password = makePassword()
    userid = str(uuid.uuid4()).upper()

    conn = pyodbc.connect(connection_string, autocommit=True)
    cursor = conn.cursor()
    cursor.execute('insert into GetMyAd_Users(id, login, password, registrationDate) values (?,?,?,getdate())',
                   userid, login, password)
    mongo_db.users.insert({'guid': userid,
                           'login': login,
                           'title': login,
                           'password': password,
                           'registrationDate': datetime.now(),
                           'manager': False
                           })
    print """
    GetMyAd Account:
        Login:    %s
        Password: %s
    """ % (login, password)



def createAdvertise(title, login, template = None):
    """Создаёт рекламную выгрузку с заголовком title для пользователя login.
    Если template <> None, то копирует оформление выгрузки template в свежесозданную.
    """
    user = mongo_db.users.find_one({'login': login})
    if not user or not user['guid']:
        print "No such user found!"
        return
    
    adv_id = str(uuid.uuid4()).upper()
    conn = pyodbc.connect(connection_string, autocommit=True)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO [AdvertiseScripts]
           ([ScriptID]
           ,[Title]
           ,[MarketID]
           ,[PartnerID]
           ,[GetMyAdUserID])
     VALUES
           (?
           ,?
           ,'CE3DE08B-AFC5-45BC-B946-7D3978AB954F'
           ,0
           ,?)
    ''', adv_id, title, user['guid'])
    
    cursor.execute('''INSERT INTO [1gb_YottosAdLoad].[dbo].[AdvertiseScriptProperties]
           ([ScriptID]
           ,[Template]
           ,[ImageWidth]
           ,[ImageHeight])
     VALUES
           (?
           ,?
           ,70
           ,70)
''', adv_id, title)
    
    mongo_db.Advertise.insert({'guid': adv_id,
                               'title': title,
                               'user': {'login': user['login'],
                                        'guid': user['guid']}
#                               'marketID': 'CE3DE08B-AFC5-45BC-B946-7D3978AB954F',
                               })
    
    if template:
        t = mongo_db.Advertise.find_one({'guid': template})
        if t and t.has_key('admaker'):
            mongo_db.Advertise.update({'guid': adv_id},
                                      {'$set': {'admaker': t['admaker']}})
            print "Template %s x %s used" % (t['admaker']['Main']['width'], t['admaker']['Main']['height'])
                                    
    
    print "Advertise created, ID: " + adv_id
    
    
def printList():
    """Выводит список всех пользователей и их выгрузок"""
    result = ''
    for user in mongo_db.users.find().sort('login'):
        result += (""" \n
========================================================
Login:        %s
Password:     %s
""" % (user['login'], user['password']))

        for ad in mongo_db.Advertise.find({'user.login': user['login']}):
            result += ("--------------------------------------------------------\n")
            result += (ad['title'] + '\n')
            try:
                w = int(re.search("[0-9]+",ad['admaker']['Main']['width']).group(0)) + 2*int(ad['admaker']['Main']['borderWidth'])
                h = int(re.search("[0-9]+",ad['admaker']['Main']['height']).group(0)) + 2*int(ad['admaker']['Main']['borderWidth'])
                print "Parse OK"
            except:
                print "Parse error!"
                w = ad['admaker']['Main']['width']
                h = ad['admaker']['Main']['height']
            if ad.has_key('admaker'):
                result += ('''<iframe src="http://rynok.yottos.com.ua/p_export.aspx?scr=%s" width="%s" height="%s" frameborder="0" scrolling="no"></iframe>\n''' \
                      % (ad['guid'], w, h))
            else:
                result += "Incorrect admaker info!\n"
        
    f = open('ads.txt', 'w')
    f.write(result.encode('utf8') + '\n')
        
                          
        


def usage():
    print "Manage Yottos GetMyAd users and ads"
    print "Usage:    Register new user:            register.py --regiser=login"
    print "          Create advertise for user:    register.py --advertise=title --user-login=login"
    print ""



def main():
        parser = OptionParser(usage=usage())
        parser.add_option("-r", "--register", help="create user with specified login", dest="register_login")
        parser.add_option("-a", "--advertise", help="creates advertise with specified title", dest="create_adv_title")
        parser.add_option("-u", "--user-login", help="use this user login", dest="login")
        parser.add_option("-t", "--template", help="use existing advertise template (guid)", dest="template_adv")
        parser.add_option("-l", "--list", help="list all users and advertises", action="store_true", default=False, dest="list")
        
        (options, args) = parser.parse_args()
        if options.register_login:
            createUser(options.register_login)
        if options.create_adv_title and not options.login:
            parser.error("Specify user login with -u option!")
        if options.create_adv_title and options.login:
            options.create_adv_title = unicode(options.create_adv_title, 'cp1251')
            createAdvertise(options.create_adv_title, options.login, options.template_adv)
        if options.list:
            printList()
            

if __name__ == "__main__":
    main()    
