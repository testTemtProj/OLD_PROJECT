#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import aiml
 
k = aiml.Kernel()
k.setTextEncoding('UTF-8')
 
k.learn("std-startup.xml")
 
k.setBotPredicate("name", u"Тони Старк")
while True:
    input = raw_input("> ")
    response = k.respond(input)
    print response
