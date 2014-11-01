# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 18:24:30 2014

@author: xm
"""

from monk.roles.configuration import Configuration
import monk.core.api as monkapi
from monk.core.engine import Engine
import logging
import monk.network.broker as mnb
import monk.network.scheduler as mns
import monk.utils.utils as ut
import os
import sys
import thread
import getopt
import platform
if platform.system() == 'Windows':
    import win32api
else:
    import signal
import datetime

logger = logging.getLogger('monk.roles.administrator')

adminBroker = None
scheduler = None
workers = {}
    
class AddUser(mnb.Task):
    def getLeastLoadedEngine(self):
        lengine = None
        lload = 100000 # a big integer
        for engine in workers.itervalues():
            if len(engine.users) < lload:
                lload = len(engine.users)
                lengine = engine
        return lengine
        
    def act(self):
        userName = self.decodedMessage.get('name','')
        if not userName:
            logger.error('empty user name {}'.format(self.decodedMessage))
            return
        user = monkapi.load_user(userName)
        if not user:
            user = monkapi.create_user(self.decodedMessage)
        leastLoadedEngine = self.getLeastLoadedEngine()
        user.partition = leastLoadedEngine.partition
        user.save()
        leastLoadedEngine.addUser(userName)
        
class RebalanceUser(mnb.Task):
    def act(self):
        #TODO:
        pass
    
class RegisterWorker(mnb.Task):
    def act(self):
        workerName = self.decodedMessage.get('name', '')
        if not workerName:
            logger.error('empty worker name {}'.format(self.decodedMessage))
            return
            
        if workerName not in workers:
            engine = monkapi.load_engine(workerName)
            if not engine:
                engine = monkapi.create_engine(self.decodedMessage)
            engine.partition = len(workers)
            engine.starttime = datetime.datetime.now()
            engine.status = 'active'
            workers[workerName] = engine
            engine.save()
        else:
            engine = workers[workerName]
        offsetToEnd = self.decodedMessage.get('offsetToEnd', 'False')
        adminBroker.produce('workerName, partition=engine.partition, offsetToEnd=offsetToEnd)
        
class UpdateWorker(mnb.Task):
    def act(self):
        workerName = self.decodedMessage.get('name', '')
        if workerName not in workers:
            logger.error('worker {} not registered yet'.format(workerName))
            return        
        # TODO:need to figure out what to update
        engine = workers[workerName]
        engine.save()

class UnregisterWorker(mnb.Task):
    def act(self):
        #TODO:currently unsupported
        pass
        
class AdminBroker(mnb.KafkaBroker):
    def acknowledge_registration(self, workerName, partition, offsetToEnd, **kwargs):
        self.produce('AcknowledgeRegistration', workername, partition=partition, offsetToEnd=offsetToEnd, kwargs)
        
    def add_user(self, userName, password='', **kwargs):
        self.produce('AddUser', userName, password=password, kwargs)
        
    def register_worker(self, **kwargs):
        address = ut.get_lan_ip()
        pid = os.getpgid()
        self.produce('RegisterWorker', '{}-{}'.format(address, pid), address=adress, pid=pid, kwargs)
    
    def update_worker(self, **kwargs):
        address = ut.get_lan_ip()
        pid = os.getpgid()
        produce('UpdateWorker', '{}-{}'.format(address, pid), kwargs)

    def unregister_worker(self, **kwargs):
        address = ut.get_lan_ip()
        pid = os.getpgid()
        produce('UnregisterWorker', '{}-{}'.format(address, pid), kwargs)

def print_help():
    print 'monkadmin.py -c <configFile>'
    
def onexit():
    adminBroker.exits()
    monkapi.exits()
    logger.info('administrator {0} is shutting down'.format(os.getpid()))

def handler(sig, hook=thread.interrupt_main):
    onexit()
    exit(1)
    
def main():
    global adminBroker, scheduler
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
    
    adminBroker = AdminBroker(config.kafkaConnectionString, config.administratorGroup, config.administratorTopic, 
                              config.administratorServerParitions, config.administratorClientPartitions)
    scheduler = mns.Scheduler([adminBroker])
    scheduler.run()

if __name__=='__main__':
    main()