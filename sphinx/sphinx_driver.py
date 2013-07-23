#!/usr/bin/python
# This Python file uses the following encoding: utf-8
# encoding: utf-8
import pymongo
import re
from binascii import crc32


def textClean(string):
    p = re.compile(u'[^А-Яа-яa-zA-Z0-9-]', re.UNICODE)
    string = p.sub(' ',string)
    return string.encode('utf-8')

db = pymongo.Connection(['yottos.ru','213.186.121.76:27018','213.186.121.199:27018']).getmyad_db
cur = db.offer.find({})
id = 0
print """<?xml version="1.0" encoding="utf-8"?><sphinx:docset>
<sphinx:schema>
<sphinx:field name="title"/>
<sphinx:field name="description"/>
<sphinx:field name="keywords"/>
<sphinx:field name="exactly_phrases"/>
<sphinx:field name="phrases"/>
<sphinx:field name="minus_words"/>
<sphinx:attr name="stitle" type="string"/>
<sphinx:attr name="sdescription" type="string"/>
<sphinx:attr name="skeywords" type="string"/>
<sphinx:attr name="sexactly_phrases" type="string"/>
<sphinx:attr name="sphrases" type="string"/>
<sphinx:attr name="guid" type="string"/>
<sphinx:attr name="match" type="string"/>
<sphinx:attr name="campaignid" type="int"/>
</sphinx:schema>"""
for item in cur:
    guid = item.get('guid').encode('utf-8')
    cguid = crc32(item.get('campaignId').encode('utf-8')) & 0xffffffff
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
<minus_words>%s</minus_words>
<stitle>%s</stitle>
<sdescription>%s</sdescription>
<skeywords>%s</skeywords>
<sexactly_phrases>%s</sexactly_phrases>
<sphrases>%s</sphrases>
<guid>%s</guid>
<match>%s</match>
<campaignid>%s</campaignid>
</sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, cguid)
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
<minus_words>%s</minus_words>
<stitle>%s</stitle>
<sdescription>%s</sdescription>
<skeywords>%s</skeywords>
<sexactly_phrases>%s</sexactly_phrases>
<sphrases>%s</sphrases>
<guid>%s</guid>
<match>%s</match>
<campaignid>%s</campaignid>
</sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, cguid)
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
<minus_words>%s</minus_words>
<stitle>%s</stitle>
<sdescription>%s</sdescription>
<skeywords>%s</skeywords>
<sexactly_phrases>%s</sexactly_phrases>
<sphrases>%s</sphrases>
<guid>%s</guid>
<match>%s</match>
<campaignid>%s</campaignid>
</sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, cguid)
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
<minus_words>%s</minus_words>
<stitle>%s</stitle>
<sdescription>%s</sdescription>
<skeywords>%s</skeywords>
<sexactly_phrases>%s</sexactly_phrases>
<sphrases>%s</sphrases>
<guid>%s</guid>
<match>%s</match>
<campaignid>%s</campaignid>
</sphinx:document>""" % (id, title, description, keywords, exactly_phrases, phrases, minus_words, title, description, keywords, exactly_phrases, phrases, guid, match, cguid)
print """</sphinx:docset>"""
