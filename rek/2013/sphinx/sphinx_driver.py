#!/usr/bin/python
# This Python file uses the following encoding: utf-8
# encoding: utf-8
import pymongo
import re
from binascii import crc32
from optparse import OptionParser
import urlparse
import urllib


def textClean(string):
    p = re.compile(u'[^А-Яа-яa-zA-Z0-9-]', re.UNICODE)
    string = p.sub(' ',string)
    return string.encode('utf-8')
def xmlCreate(mode):
    db = pymongo.Connection(['yottos.ru','213.186.121.76:27018','213.186.121.199:27018']).getmyad_db
    if mode == "worker":
        cur = db.offer.find({})
        id = 0
        print """<?xml version="1.0" encoding="utf-8"?><sphinx:docset>
        <sphinx:schema>
        <sphinx:field name="title"/>
        <sphinx:field name="description"/>
        <sphinx:field name="keywords"/>
        <sphinx:field name="exactly_phrases"/>
        <sphinx:field name="phrases"/>
        <sphinx:field name="minuswords"/>
        <sphinx:attr name="stitle" type="string"/>
        <sphinx:attr name="sdescription" type="string"/>
        <sphinx:attr name="skeywords" type="string"/>
        <sphinx:attr name="sexactly_phrases" type="string"/>
        <sphinx:attr name="sphrases" type="string"/>
        <sphinx:attr name="guid" type="string"/>
        <sphinx:attr name="match" type="string"/>
        <sphinx:attr name="fguid" type="int"/>
        </sphinx:schema>"""
        for item in cur:
            guid = item.get('guid').encode('utf-8')
            fguid = crc32(item.get('guid').encode('utf-8')) & 0xffffffff
            minus_words = " ".join(item.get('minus_words',[])).encode('utf-8')
            id +=1
            title = textClean(item.get('title'))
            description = textClean(item.get('description'))
            keywords = ''
            exactly_phrases = ''
            phrases = ''
            match = 'nomatch'
            print """<sphinx:document id="%s">
        <title>%s</title>
        <description>%s</description>
        <keywords>%s</keywords>
        <exactly_phrases>%s</exactly_phrases>
        <phrases>%s</phrases>
        <minuswords>%s</minuswords>
        <stitle>%s</stitle>
        <sdescription>%s</sdescription>
        <skeywords>%s</skeywords>
        <sexactly_phrases>%s</sexactly_phrases>
        <sphrases>%s</sphrases>
        <guid>%s</guid>
        <match>%s</match>
        <fguid>%s</fguid>
        </sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, fguid)
            for value in item.get('keywords',[]):
                id +=1
                title = ''
                description = ''
                keywords = value.encode('utf-8')
                exactly_phrases = ''
                phrases = ''
                match = 'broadmatch'
                print """<sphinx:document id="%s">
        <title>%s</title>
        <description>%s</description>
        <keywords>%s</keywords>
        <exactly_phrases>%s</exactly_phrases>
        <phrases>%s</phrases>
        <minuswords>%s</minuswords>
        <stitle>%s</stitle>
        <sdescription>%s</sdescription>
        <skeywords>%s</skeywords>
        <sexactly_phrases>%s</sexactly_phrases>
        <sphrases>%s</sphrases>
        <guid>%s</guid>
        <match>%s</match>
        <fguid>%s</fguid>
        </sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, fguid)
            for value in item.get('exactly_phrases',[]):
                id +=1
                title = ''
                description = ''
                keywords = ''
                exactly_phrases = value.encode('utf-8')
                phrases = ''
                match = 'exactmatch'
                print """<sphinx:document id="%s">
        <title>%s</title>
        <description>%s</description>
        <keywords>%s</keywords>
        <exactly_phrases>%s</exactly_phrases>
        <phrases>%s</phrases>
        <minuswords>%s</minuswords>
        <stitle>%s</stitle>
        <sdescription>%s</sdescription>
        <skeywords>%s</skeywords>
        <sexactly_phrases>%s</sexactly_phrases>
        <sphrases>%s</sphrases>
        <guid>%s</guid>
        <match>%s</match>
        <fguid>%s</fguid>
        </sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, fguid)
            for value in item.get('phrases',[]):
                id +=1
                title = ''
                description = ''
                keywords = ''
                exactly_phrases = ''
                phrases = value.encode('utf-8')
                match = 'phrasematch'
                print """<sphinx:document id="%s">
        <title>%s</title>
        <description>%s</description>
        <keywords>%s</keywords>
        <exactly_phrases>%s</exactly_phrases>
        <phrases>%s</phrases>
        <minuswords>%s</minuswords>
        <stitle>%s</stitle>
        <sdescription>%s</sdescription>
        <skeywords>%s</skeywords>
        <sexactly_phrases>%s</sexactly_phrases>
        <sphrases>%s</sphrases>
        <guid>%s</guid>
        <match>%s</match>
        <fguid>%s</fguid>
        </sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, fguid)
    elif (mode == 'retargeting'):
        cur = db.offer.find({"retargeting": True})
        id = 0
        print """<?xml version="1.0" encoding="utf-8"?><sphinx:docset>
        <sphinx:schema>
        <sphinx:field name="url"/>
        <sphinx:field name="domain"/>
        <sphinx:field name="urlpatch"/>
        <sphinx:field name="urlparam"/>
        <sphinx:field name="title"/>
        <sphinx:field name="description"/>
        <sphinx:field name="keywords"/>
        <sphinx:field name="exactly_phrases"/>
        <sphinx:field name="phrases"/>
        <sphinx:attr name="guid" type="string"/>
        <sphinx:attr name="accountid" type="string"/>
        <sphinx:attr name="faccountid" type="int"/>
        </sphinx:schema>"""
        for item in cur:
            id +=1
            guid = item.get('guid').encode('utf-8')
            url = item.get('url').encode('utf-8')
            url_list = list(urlparse.urlparse(url))
            domain = url_list[1]
            url_patch = url_list[2]
            url_param = url_list[4]
            title = textClean(item.get('title'))
            description = textClean(item.get('description'))
            keywords = ' '.join(item.get('keywords',[])).encode('utf-8')
            exactly_phrases = ' '.join(item.get('exactly_phrases',[])).encode('utf-8')
            phrases = ' '.join(item.get('phrases',[])).encode('utf-8')
            accountId  = item.get('accountId','1').encode('utf-8')
            fAccountId = crc32(accountId) & 0xffffffff
            print """<sphinx:document id="%s">
        <url><![CDATA[[%s]]></url>
        <domain><![CDATA[[%s]]></domain>
        <urlpatch><![CDATA[[%s]]></urlpatch>
        <urlparam><![CDATA[[%s]]></urlparam>
        <title>%s</title>
        <description>%s</description>
        <keywords>%s</keywords>
        <exactly_phrases>%s</exactly_phrases>
        <phrases>%s</phrases>
        <guid>%s</guid>
        <accountid>%s</accountid>
        <faccountid>%s</faccountid>
        </sphinx:document>""" % (id, url, domain , url_patch, url_param, title, description, keywords, exactly_phrases, phrases, guid, accountId, fAccountId)
    else:
        print
    print """</sphinx:docset>"""
    
if __name__ == '__main__':
    parser = OptionParser(version='1.0', description='Generate XML document for Sphinx index', usage='usage: %prog [options]')
    parser.add_option('-m',
                      '--mode',
                      default='worker',
                      help='generate data mode: worker, retargeting \t[default: %default]'
                      )
    (options, args) = parser.parse_args()
    xmlCreate(options.mode)
