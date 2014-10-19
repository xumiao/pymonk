# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 18:24:30 2014

@author: xm
"""

from monk.roles.configuration import Configuration
import monk.core.api as monkapi
import pymongo as pm
import logging
import monk.network.broker as mnb
import monk.network.scheduler as mns
import os
import sys
import thread
import getopt
import platform
if platform.system() == 'Windows':
    import win32api
else:
    import signal
    
logger = logging.getLogger('monk.roles.administrator')

broker = None
scheduler = None

class AddUser(mnb.Task):
    def act(self):
        monkapi.create_user(self.decodedMessage)

class RebalanceUser(mnb.Task):
    def act(self):
        pass
    
class RegisterWorker(mnb.Task):
    def act(self):
        monkapi.create_engine(self.decodedMessage)
    
class UpdateWorker(mnb.Task):
    def act(self):
        monkapi.update_engine(self.decodedMessage)

class UnregisterWorker(mnb.Task):
    def act(self):
        pass
        
def print_help():
    print 'monkadmin.py -c <configFile>'
    
def onexit():
    broker.exits()
    monkapi.exits()
    logger.info('worker {0} is shutting down'.format(os.getpid()))

def handler(sig, hook = thread.interrupt_main):
    broker.exits()
    monkapi.exits()
    logger.info('worker {0} is shutting down'.format(os.getpid()))
    exit(1)
    
def main():
    global broker, scheduler
    configFile = 'monk_config.yml'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hc:',['configFile='])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ('-c', '--configFile'):
            configFile = arg
    config = Configuration(configFile, "administrator", str(os.getpid()))
    monkapi.initialize(config)
    if platform.system() == 'Windows':
        win32api.SetConsoleCtrlHandler(handler, 1)
    else:
        signal.signal(signal.SIGINT, onexit)
    
    broker = mnb.KafkaBroker(config.kafkaConnectionString, config.administratorGroup, 
                             config.administratorTopic, config.administratorParitions)
    scheduler = mns.Scheduler([broker])
    scheduler.run()
