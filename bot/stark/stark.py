#!/usr/bin/python
# -*- coding: UTF8 -*-
import aiml
import os.path

k = aiml.Kernel()
#if os.path.isfile("cerebro.brn"): 
#    k.bootstrap(brainFile = "cerebro.brn")
#else:
k.loadSubs("startup.xml")
k.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml")
k.saveBrain("cerebro.brn")
k.loadBrain("cerebro.brn")


while True: 
    user_input = raw_input(" > ")
    response = k.respond(user_input)
    print response
