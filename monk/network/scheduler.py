# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 00:06:55 2014

@author: xm
"""
import monk.core.api as monkapi
from Queue import PriorityQueue
import time
import logging
import platform
if platform.system() == 'Windows':
    import win32api
else:
    import signal
import thread

logger = logging.getLogger('monk.scheduler')


class Scheduler(object):
    WAIT_TIME=0.1
    MAX_QUEUE_SIZE=100000
    MAINTENANCE_INTERVAL=10000
    
    def __init__(self, schedulerName, brokers):
        self.brokers = brokers
        self.pq = PriorityQueue(self.MAX_QUEUE_SIZE)
        self.lastMaintenance = time.time()
        self.schedulerName = schedulerName
        if platform.system() == 'Windows':
            win32api.SetConsoleCtrlHandler(self.handler, 1)
        else:
            signal.signal(signal.SIGINT, self.handler)
        
    def maintanence(self):
        self.lastMaintenance = time.time()

    def handler(self, sig, hook=thread.interrupt_main):
        self.onexit()
        exit(1)
        
    def onexit(self):
        for broker in self.brokers:
            broker.close()
        monkapi.exits()
        logger.info('{} is shutting down'.format(self.schedulerName))
        
    def run(self):
        while True:
            wait = True
            if self.pq.queue:
                priority, task = self.pq.get()
                task.act()
                wait = False
            for broker in self.brokers:
                task = broker.consumeOne()
                if task:
                    self.pq.put((task.priority, task))
                    wait = False
            if time.time() - self.lastMaintenance > Scheduler.MAINTENANCE_INTERVAL:
                self.maintanence()
                wait = False
            if wait:
                time.sleep(Scheduler.WAIT_TIME)
            