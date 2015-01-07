# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 20:44:58 2015

@author: xm
"""

from monk.roles.monitor import MonitorBroker
import numpy as np

print 'creating monitor broker'
mb = MonitorBroker('monkbus.cloudapp.net:9092,monkbus.cloudapp.net:9093,monkbus.cloudapp.net:9094','monkTestMonitor',producerType=1,producerPartitions=[0])

values = np.random.rand(1000)
def choose_user(x):
    if x >  0.5:
        return 'user1'
    else:
        return 'user2'

users = map(choose_user, np.random.rand(1000))
for i in range(1000):
    value = values[i]
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
