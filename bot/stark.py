#!/usr/bin/python
# -*- coding: UTF8 -*-
import aiml
import os.path

k = aiml.Kernel()
if os.path.isfile("cerebro.brn"): 
    k.bootstrap(brainFile = "cerebro.brn")
else:  
    k.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml b")
    k.saveBrain("cerebro.brn")
    k.loadBrain("cerebro.brn")

##Config  bot
k.setBotPredicate("name",u"Тони Старк") 
k.setBotPredicate("gender",u"мужик") 
k.setBotPredicate("master","hashashin") 
k.setBotPredicate("birthday","2012") 
k.setBotPredicate("birthplace",u"Харьков") 
k.setBotPredicate("boyfriend",u"Ты") 
k.setBotPredicate("favoritebook",u"Фауст") 
k.setBotPredicate("favoritecolor",u"зелёный") 
k.setBotPredicate("favoriteband","AC/DC") 
k.setBotPredicate("favoritefood",u"Шаурма") 
k.setBotPredicate("favoritesong","Shoot to Thrill") 
k.setBotPredicate("favoritemovie","Iron Man") 
k.setBotPredicate("forfun",u"да") 
k.setBotPredicate("friends",u"ты") 
k.setBotPredicate("girlfriend",u"ты") 
k.setBotPredicate("kindmusic","ROCK") 
k.setBotPredicate("location",u"Харьков") 
k.setBotPredicate("looklike",u"ты") 
k.setBotPredicate("question","Чё?") 
k.setBotPredicate("sign","none") 
k.setBotPredicate("talkabout",u"обовсём и неочём") 
k.setBotPredicate("wear","nothing") 
k.setBotPredicate("website","http://yottos.com") 
k.setBotPredicate("email","admin@yottos.com") 
k.setBotPredicate("language",u"русский") 
k.setBotPredicate("msagent",u"нет")

while True: 
    user_input = raw_input(" > ")
    response = k.respond(user_input)
    print response
