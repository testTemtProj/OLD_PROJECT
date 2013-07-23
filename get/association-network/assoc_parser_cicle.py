#!/usr/bin/env python2
#-*- coding: utf-8 -*-

from httplib2 import Http
from urllib import urlencode
import json
import pymysql


db = pymysql.connect(user='root', passwd='123qwe', db='test', use_unicode=True, charset='utf8')
cursor = db.cursor()

http = Http()
host_info = 'http://sociation.org/ajax/get_word_info/'
host_assoc = 'http://sociation.org/ajax/word_associations/'
w = 0

def get_word_info(word):
    global http, host_info
    info_response, info_content = http.request(host_info, "POST", urlencode({"word":word.encode('utf8')}))
    word_info = json.loads(info_content)['word']
    return word_info

not_complete = True
while (not_complete):
    cursor.execute('select word from word where complete = 0')
    word = cursor.fetchone()[0]
    word_info = get_word_info(word)
    w += 1
    print 'Words associated:', w
    if not cursor.execute("select id_wrd from word where word = '%s'" % (word)):
        cursor.execute("insert into word (word, associated, as_association) values ('%s', %d, %d)"\
                           % (word_info['name'].encode('utf-8'), word_info['associations_count'], word_info['as_association_count']))
        
        
    assoc_response_to, assoc_content_to = http.request(host_assoc, "POST", urlencode({"word":word.encode('utf8'), "back":0, "max_count":0}))
    assoc_to = json.loads(assoc_content_to)['associations']
    
    assoc_response_back, assoc_content_back = http.request(host_assoc, "POST", urlencode({"word":word.encode('utf8'), "back":1, "max_count":0}))
    assoc_back = json.loads(assoc_content_back)['associations']
    
    for i in assoc_to:
        if not cursor.execute("select id_wrd from word where word = '%s'" % (i['name'])):
            assoc_wrd_info = get_word_info(i['name'])
            cursor.execute("insert into word(word, associated,  as_association, complete) values('%s', %d, %d, %d)"\
                               % (assoc_wrd_info['name'], assoc_wrd_info['associations_count'], assoc_wrd_info['as_association_count'], 0))

        if not cursor.execute("select id_assoc from association where id_start_wrd = (select id_wrd from word where word='%s') and id_finish_wrd = (select id_wrd from word where word='%s')"\
                                  % (word,i['name'])):
            cursor.execute('select id_wrd from word where word = "%s"' %(word))
            start_wrd_id = cursor.fetchone()[0]
            cursor.execute('select id_wrd from word where word = "%s"' %(i['name']))
            finish_wrd_id = cursor.fetchone()[0]
            cursor.execute('insert into association(id_start_wrd, id_finish_wrd, assoc_count, popularity) values(%d, %d, %d, %d)' % (start_wrd_id, finish_wrd_id, i['associations_count'], i['popularity']))

        else: 
            continue

    for i in assoc_back:
        if not cursor.execute("select id_wrd from word where word = '%s'" % (i['name'])):
            assoc_wrd_info = get_word_info(i['name'])
            cursor.execute("insert into word(word, associated,  as_association, complete) values('%s', %d, %d, %d)"\
                               % (assoc_wrd_info['name'], assoc_wrd_info['associations_count'], assoc_wrd_info['as_association_count'], 0))

        if not cursor.execute("select id_assoc from association where id_start_wrd = (select id_wrd from word where word='%s') and id_finish_wrd = (select id_wrd from word where word='%s')"\
                                  % (i['name'], word)):
            cursor.execute('select id_wrd from word where word = "%s"' %(i['name']))
            start_wrd_id = cursor.fetchone()[0]
            cursor.execute('select id_wrd from word where word = "%s"' %(word))
            finish_wrd_id = cursor.fetchone()[0]
            cursor.execute('insert into association(id_start_wrd, id_finish_wrd, assoc_count, popularity) values(%d, %d, %d, %d)' % (start_wrd_id, finish_wrd_id, i['associations_count'], i['popularity']))

        else: 
            continue

    cursor.execute("update word set complete = 1 where word = '%s'" % (word))
    cursor.execute('commit')
    not_complete = False if not cursor.execute('select word from word where complete = 0') else True
    print not_complete
