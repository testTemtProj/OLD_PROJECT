#!/usr/bin/python
import nn
mynet=nn.searchnet()
AllGroup=[1, 2, 3, 4]
UserParamValyeN = [10001, 20002, 30001, 40001, 50005, 60095, 70001, 82156, 90082, 10006, 11093, 12003]
#UserParamValyeN = [10001, 20002]
print '1, 2, 3, 4 true = 3'
print mynet.getresult(UserParamValyeN, AllGroup)
