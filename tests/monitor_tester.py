# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 20:44:58 2015

@author: xm
"""

from monk.roles.monitor import MonitorBroker
import numpy as np
import logging
N = 1000
print 'creating monitor broker'
mb = MonitorBroker('monkbus.cloudapp.net:9092,monkbus.cloudapp.net:9093,monkbus.cloudapp.net:9094','monkTestMonitor',producerType=1)

for i in range(N):
    value = np.random.rand() 
    if np.random.rand() > 0.5:
        pos = 'True'
    else:
        pos = 'False'
    if np.random.rand() > 0.5:
        user = 'user1'
    else:
        user = 'user2'
    mb.measure('test', value, pos, user)
    print 'test', value, pos, user
mb.close()
