#!/usr/bin/python
import nn
mynet=nn.searchnet('nn.db')
mynet.maketables()
UserParamValye1, UserParamValye2, UserParamValyeN = 101, 102, 103
OfferGroup1, OfferGroup2, OfferGroupN = 201, 202, 203
AllGroup=[OfferGroup1, OfferGroup2, OfferGroupN]
print 'Training network to association'
print 'UserParamValye1, UserParamValyeN to group OfferGroup1'
print 'UserParamValye2, UserParamValyeN to group OfferGroup2'
print 'UserParamValye1 to group OfferGroupN'
for i in range(30):
    mynet.trainquery([UserParamValye1, UserParamValyeN], AllGroup, OfferGroup1)
    mynet.trainquery([UserParamValye2, UserParamValyeN], AllGroup, OfferGroup2)
    mynet.trainquery([UserParamValye1], AllGroup, OfferGroupN)
print
print
print 'Test Association UserParamValye1, UserParamValyeN to group'
print 'OfferGroup1,    OfferGroup2,    OfferGroupN'
print mynet.getresult([UserParamValye1, UserParamValyeN], AllGroup)
print
print 'Test Association UserParamValye2, UserParamValyeN to group'
print 'OfferGroup1,    OfferGroup2,    OfferGroupN'
print mynet.getresult([UserParamValye2, UserParamValyeN], AllGroup)
print
print 'Test Association UserParamValye1 to group'
print 'OfferGroup1,    OfferGroup2,    OfferGroupN'
print mynet.getresult([UserParamValye1], AllGroup)
print
print 'Test Predskazaniy UserParamValyeN to group'
print 'OfferGroup1,    OfferGroup2,    OfferGroupN'
print mynet.getresult([UserParamValyeN], AllGroup)
import httpagentparser
s = 'Opera/9.80 (Android 2.2.1; Linux; Opera Tablet/ADR-1111101157; U; ru) Presto/2.9.201 Version/11.50'
print httpagentparser.detect(s)
