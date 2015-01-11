# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 20:44:58 2015

@author: xm
"""

from monk.roles.monitor import MonitorBroker
import numpy as np
from monk.roles.configuration import config_logging

config_logging('log_config.yml')

N = 10000
print 'creating monitor broker'
mb = MonitorBroker(kafkaHost='monkbus.cloudapp.net:9092,monkbus.cloudapp.net:9093,monkbus.cloudapp.net:9094',
                   kafkaGroup='monkTestMonitor',
                   kafkaTopic='monkTestMonitor',
                   producerType=1,
                   producerPartitions=[0])

for i in range(N):
    value = np.random.rand() 
    if np.random.rand() > 0.5:
        label = 1
    else:
        label = -1
    user = ''.join(['user', str(int(np.random.rand() * 10))])
    mb.measure('test', value, label, user)
    print 'test', value, label, user
mb.close()
