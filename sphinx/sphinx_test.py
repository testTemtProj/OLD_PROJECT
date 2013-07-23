#!/usr/bin/python
# This Python file uses the following encoding: utf-8
# encoding: utf-8
from sphinxapi import *
import sys, time
from pprint import pprint
from binascii import crc32
import zlib
host = '10.0.0.8'
port = 9312
index = '*'
Weights = {'title':50,'description':30}
#iltercol = 'offerguidcrc'
#iltervals = [244,]
mode = SPH_MATCH_EXTENDED2
cl = SphinxClient()
cl.SetServer ( host, port )
cl.SetMatchMode ( mode )
#cl.SetFieldWeights ( Weights )
cl.SetLimits(0,200)
#cl.SetFilter ( filtercol, filtervals, 1 )
#q = '''@(title,description) "фа настройки  разде  уме  час  просчет"/2'''
#res = cl.Query ( q, index )
#if res.has_key('matches'):
#    n = 1
#    print '\nMatches:'
#    for match in res['matches']:
#        attrsdump = ''
#        for attr in res['attrs']:
#            attrname = attr[0]
#            attrtype = attr[1]
#            value = match['attrs'][attrname]
#            attrsdump = '%s, %s=%s' % ( attrsdump, attrname, value )
#
#        print '%d. doc_id=%s, weight=%d%s' % (n, match['id'], match['weight'], attrsdump)
#        n += 1

#q = '''@description файле | настройки | проксирования | haproxy'''
#res = cl.Query ( q, index )
#if res.has_key('matches'):
#    n = 1
#    print '\nMatches:'
#    for match in res['matches']:
#        attrsdump = ''
#        for attr in res['attrs']:
#            attrname = attr[0]
#            attrtype = attr[1]
#            value = match['attrs'][attrname]
#            attrsdump = '%s, %s=%s' % ( attrsdump, attrname, value )

#        print '%d. doc_id=%s, weight=%d%s' % (n, match['id'], match['weight'], attrsdump)
#        n += 1

#q = '''@description "файле настройки проксирования haproxy"~5'''
#mode = SPH_MATCH_EXTENDED
#cl = SphinxClient()
#cl.SetServer ( host, port )
#cl.SetMatchMode ( mode )
#res = cl.Query ( q, index )
#if res.has_key('matches'):
#    n = 1
#    print '\nMatches:'
#    for match in res['matches']:
#        attrsdump = ''
#        for attr in res['attrs']:
#            attrname = attr[0]
#            attrtype = attr[1]
#            value = match['attrs'][attrname]
#            attrsdump = '%s, %s=%s' % ( attrsdump, attrname, value )
#
#        print '%d. doc_id=%s, weight=%d%s' % (n, match['id'], match['weight'], attrsdump)
#        n += 1

#q = '''@description "<<настройки <<проксирования <<в <<конфигурационном"~1'''
#mode = SPH_MATCH_EXTENDED
#cl = SphinxClient()
#cl.SetServer ( host, port )
#cl.SetMatchMode ( mode )
#res = cl.Query ( q, index )
#if res.has_key('matches'):
#    n = 1
#    print '\nMatches:'
#    for match in res['matches']:
#        attrsdump = ''
#        for attr in res['attrs']:
#            attrname = attr[0]
#            attrtype = attr[1]
#            value = match['attrs'][attrname]
#            attrsdump = '%s, %s=%s' % ( attrsdump, attrname, value )
#
#        print '%d. doc_id=%s, weight=%d%s' % (n, match['id'], match['weight'], attrsdump)
#        n += 1
#q = '''@(title,description) "фа настройки  разде  уме  час  просчет"/2'''
#cl.AddQuery(q, index )
#q = '''@description файле | настройки | проксирования | haproxy'''
#cl.AddQuery(q, index )
#q = '''@description "файле настройки проксирования haproxy"~5'''
#cl.AddQuery(q, index )
#q = '''@description "<<настройки <<проксирования <<в <<конфигурационном"~1'''
#cl.AddQuery(q, index )
#q = '''(@exactly_phrases "<<настройки <<проксирования <<в <<конфигурационном"~1) | (@(title,description) "фа настройки  разде  уме  час  просчет"/2) | ('@keywords файле | настройки | проксирования | haproxy) | (@phrases "файле настройки проксирования haproxy"~5)'''
#q = '''((@exactly_phrases "<<Установка настройка конфигурация Linux Windows Apache Nginx Bind MongoDB Mysql оптимизация серверов сервера сервер данных MySql MsSql Oracle MongoBD FreeBSD Server DirectAdmin ispmanager DDOS openfire jabber mysql mssql mongodb iptables bind hyper apply proftpd centos debian zabbix agent nginx exim apache ubuntu raid mdadm dmraid xinetd subversion "~1) | (@(title,description) "Установка настройка конфигурация Linux Windows Apache Nginx Bind MongoDB Mysql оптимизация серверов сервера сервер данных MySql MsSql Oracle MongoBD FreeBSD Server DirectAdmin ispmanager DDOS openfire jabber mysql mssql mongodb iptables bind hyper apply proftpd centos debian zabbix agent nginx exim apache ubuntu raid mdadm dmraid xinetd subversion"/2) | (@keywords  Установка настройка конфигурация Linux Windows Apache Nginx Bind MongoDB Mysql оптимизация серверов сервера сервер данных MySql MsSql Oracle MongoBD FreeBSD Server DirectAdmin ispmanager DDOS openfire jabber mysql mssql mongodb iptables bind hyper apply proftpd centos debian zabbix agent nginx exim apache ubuntu raid mdadm dmraid xinetd subversion| ) | (@phrases "Установка настройка конфигурация Linux Windows Apache Nginx Bind MongoDB Mysql оптимизация серверов сервера сервер данных MySql MsSql Oracle MongoBD FreeBSD Server DirectAdmin ispmanager DDOS openfire jabber mysql mssql mongodb iptables bind hyper apply proftpd centos debian zabbix agent nginx exim apache ubuntu raid mdadm dmraid xinetd subversion"~5)) -(@minus_wordsУстановка настройка конфигурация Linux Windows Apache Nginx Bind MongoDB Mysql оптимизация серверов сервера сервер данных MySql MsSql Oracle MongoBD FreeBSD Server DirectAdmin ispmanager DDOS openfire jabber mysql mssql mongodb iptables bind hyper apply proftpd centos debian zabbix agent nginx exim apache ubuntu raid mdadm dmraid xinetd subversion)'''
#q = '''((@exactly_phrases "<<Установка <<настройка <<конфигурация <<Linux <<Windows"~1) | (@(title,description) "Установка настройка конфигурация Linux Windows Apache оптимизация серверов сервера сервер данных"/2) | (@keywords  настройка| haproxy| конфигурация| оптимизация| серверов| bind| hyper| apply| proftpd| centos| debian ) | (@phrases "Установка настройка конфигурация Linux"~5)) -(@minus_words настройка конфигурация Linux мама)'''
#q = ''' ((@exactly_phrases "<<Софт <<RAID <<зеркало <<mirror <<Centos <<technologies <<life <<Пошаговая <<настройка <<софт <<centos <<raid <<soft <<linux "~1) | (@title "Софт RAID зеркало mirror Centos technologies life Пошаговая настройка софт centos raid soft linux haproxy"/1)| (@description "Софт RAID зеркало mirror Centos technologies life Пошаговая настройка софт centos raid soft linux"/2) | (@keywords  Софт |RAID |зеркало |mirror |Centos |technologies |life |Пошаговая |настройка |софт |centos |raid |soft |linux | haproxy ) | (@phrases "Софт RAID зеркало mirror Centos technologies life Пошаговая настройка софт centos raid soft linux haproxy"~5)) -(@minus_words "Софт RAID зеркало mirror Centos technologies life Пошаговая настройка софт centos raid soft linux"/1)'''
q = '''@keywords ( настройка | linux | haproxy ) @!(keywords,title,description,exactly_phrases,phrases) -настройка -linux'''
cl.AddQuery(q, index )
res = cl.RunQueries()
pprint(res)
for item in res:
    if item.has_key('matches'):
        n = 1
        print '\nMatches:'
        for match in item['matches']:
            attrsdump = ''
            for attr in item['attrs']:
                attrname = attr[0]
                attrtype = attr[1]
                value = match['attrs'][attrname]
                attrsdump = '%s, %s=%s' % ( attrsdump, attrname, value )

            print '%d. doc_id=%s, weight=%d%s' % (n, match['id'], match['weight'], attrsdump)
            n += 1

#a = crc32('07625e69-0696-479f-b971-8342c2a64e9d') & 0xffffffff
#b = crc32('4e7b2e82-149d-439f-97fb-53257bd38fb7') & 0xffffffff
#c = zlib.crc32('07625e69-0696-479f-b971-8342c2a64e9d') & 0xffffffff
#d = zlib.crc32('4e7b2e82-149d-439f-97fb-53257bd38fb7') & 0xffffffff
#print a, "  2381374845 ", c
#print b, "  2670658149 ", d
