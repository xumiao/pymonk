# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 00:06:55 2014

@author: xm
"""
from Queue import PriorityQueue
import time

class Scheduler(object):
    WAIT_TIME=0.1
    MAX_QUEUE_SIZE=100000
    MAINTENANCE_INTERVAL=10000
    
    def __init__(self, brokers):
        self.brokers = brokers
        self.pq = PriorityQueue(self.MAX_QUEUE_SIZE)
        self.lastMaintenance = time.time()
        
    def maintanence(self):
        self.lastMaintenance = time.time()
    
    def run(self):
        while True:
            wait = True
            if self.pq.queue:
                priority, task = self.pq.get()
                task.act()
                wait = False
            for broker in self.brokers:
                priority, task = broker.consumeOne()
                if task:
                    self.pq.put((priority, task))
                    wait = False
            if time.time() - self.lastMaintenance > Scheduler.MAINTENANCE_INTERVAL:
                self.maintanence()
                wait = False
            if wait:
                time.sleep(Scheduler.WAIT_TIME)
            