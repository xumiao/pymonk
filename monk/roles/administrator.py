# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 18:24:30 2014

@author: xm
"""

from monk.roles.configuration import Configuration
import monk.core.api as monkapi
import logging
import monk.network.broker as mnb
import monk.network.scheduler as mns
from monk.core.user import User
from monk.core.engine import Engine
import monk.core.constants as cons
import monk.utils.utils as ut
import sys, os
import getopt
import datetime
from itertools import cycle

logger = logging.getLogger('monk.roles.administrator')

adminBroker = None
scheduler = None
workers = {}
maxNumWorkers = 32
    
class AddUser(mnb.Task):
    def get_least_loaded_engine(self):
        lengine = None
        lload = 100000 # a big integer
        for engine in workers.itervalues():
            if engine.is_active() and len(engine.users) < lload:
                lload = len(engine.users)
                lengine = engine
        return lengine
        
    def act(self):
        userName = self.decodedMessage.get(User.NAME,'')
        if not userName:
            logger.error('empty user name {}'.format(self.decodedMessage))
            return
        user = monkapi.load_user(userName)
        if not user:
            leastLoadedEngine = self.get_least_loaded_engine()
            userScript = {User.NAME      : userName,\
                          User.CREATOR   : cons.DEFAULT_CREATOR,\
                          User.FPART     : leastLoadedEngine.partition,\
                          User.FFNAME    : self.decodedMessage.get(User.FFNAME),\
                          User.FGENDER   : self.decodedMessage.get(User.FGENDER),\
                          User.FLNAME    : self.decodedMessage.get(User.FLNAME),\
                          User.FMName    : self.decodedMessage.get(User.FMName),\
                          User.FPASSWORD : self.decodedMessage.get(User.FPASSWORD),\
                          User.FYEAR     : int(self.decodedMessage.get(User.FYEAR, '1900'))}
            user = monkapi.create_user(userScript)
            leastLoadedEngine.add_user(userName)

mnb.register(AddUser)

class DeleteUser(mnb.Task):
    def act(self):
        userName = self.decodedMessage.get(User.NAME, '')
        if not userName or not monkapi.delete_user(userName):
            logger.info('trying to delete non-existant user {}'.format(userName))

mnb.register(DeleteUser)

class UpdateUser(mnb.Task):
    def act(self):
        userName = self.decodedMessage.get(User.NAME, '')
        if not userName:
            logger.error('empty user name {}'.format(self.decodedMessage))
            return
        user = monkapi.load_user(userName)
        if not user:
            logger.error('user is not registered {}'.format(self.decodedMessage))
            return
        user._setattr(User.FFNAME,    self.decodedMessage.get(User.FFNAME))
        user._setattr(User.FGENDER,   self.decodedMessage.get(User.FGENDER))
        user._setattr(User.FLNAME,    self.decodedMessage.get(User.FLNAME))
        user._setattr(User.FMName,    self.decodedMessage.get(User.FMName))
        user._setattr(User.FPASSWORD, self.decodedMessage.get(User.FPASSWORD))
        user._setattr(User.FYEAR,     self.decodedMessage.get(User.FYEAR), lambda x: int(x))
        user.save()

mnb.register(UpdateUser)

class RebalanceUsers(mnb.Task):
    def act(self):
        activeEngines = filter(lambda engine: engine.is_active(), workers.itervalues())
        def extend(x,y):
            x.extend(y.users)
            y.users = []
            return x
        activeUsers = reduce(extend, activeEngines, [])
        iterEngine = cycle(activeEngines)
        for userName in activeUsers:
            engine = iterEngine.next()
            user = monkapi.load_user(userName)
            user.partition = engine.partition
            user.save()
            engine.add_user(userName)
    
mnb.register(RebalanceUsers)
    
class RegisterWorker(mnb.Task):
    def next_partition(self):
        if len(workers) < maxNumWorkers:
            return len(workers)
        else:
            oldest = datetime.now()
            oldestWorker = None
            for worker in workers:
                if worker.lastModified < oldest:
                    oldestWorker = worker
                    oldest = worker.lastModified
            return oldestWorker.partition
            
    def act(self):
        global workers
        workerName = self.decodedMessage.get('name', '')
        if not workerName:
            logger.error('empty worker name {}'.format(self.decodedMessage))
            return
        logger.info('worker {} registering'.format(workerName))
        if workerName not in workers:
            engine = monkapi.load_engine(workerName)
            if not engine:
                engineScript = {Engine.NAME: workerName,\
                                Engine.CREATOR: cons.DEFAULT_CREATOR,\
                                Engine.FPARTITION: self.next_partition(),\
                                Engine.FSTARTTIME: datetime.datetime.now(),\
                                Engine.FPID: self.decodedMessage.get(Engine.FPID),\
                                Engine.FSTATUS: cons.STATUS_ACTIVE}
                engine = monkapi.create_engine(engineScript)
            workers[workerName] = engine
        else:
            engine = workers[workerName]
        offsetToEnd = self.decodedMessage.get('offsetToEnd', 'False')
        adminBroker.acknowledge_registration(workerName, engine.partition, offsetToEnd)

mnb.register(RegisterWorker)
        
class UpdateWorker(mnb.Task):
    def act(self):
        workerName = self.decodedMessage.get('name', '')
        if workerName not in workers:
            logger.error('worker {} not registered yet'.format(workerName))
            return
        engine = workers[workerName]
        engine._setattr(Engine.FADDRESS, self.decodedMessage.get(Engine.FADDRESS))
        engine._setattr(Engine.FPID,     self.decodedMessage.get(Engine.FPID))
        engine._setattr(Engine.FSTATUS,  self.decodedMessage.get(Engine.FSTATUS))
        engine.save()

mnb.register(UpdateWorker)

class UnregisterWorker(mnb.Task):
    def act(self):
        workerName = self.decodedMessage.get('name', '')
        if not workerName:
            logger.error('empty worker name {}'.format(self.decodedMessage))
            return
        logger.info('worker {} unregistering'.format(workerName))
        if workerName in workers:
            engine = workers[workerName]
            engine._setattr(Engine.FSTATUS,  cons.STATUS_INACTIVE)
            engine._setattr(Engine.FENDTIME, datetime.datetime.now())
            engine.save()

mnb.register(UnregisterWorker)
        
class AdminBroker(mnb.KafkaBroker):
    def acknowledge_registration(self, workerName, partition, offsetToEnd, **kwargs):
        self.produce('AcknowledgeRegistration', workerName, partition=partition, offsetToEnd=offsetToEnd, **kwargs)
        
    def add_user(self, userName, password='', **kwargs):
        self.produce('AddUser', userName, password=password, **kwargs)
    
    def update_user(self, userName, password='', **kwargs):
        self.produce('UpdateUser', userName, password=password, **kwargs)
        
    def delete_user(self, userName, password='', **kwargs):
        self.produce('DeleteUser', userName, password=password, **kwargs)
    
    def rebalance_users(self, userName, password='', **kwargs):
        self.produce('RebalanceUsers', userName, password=password, **kwargs)
        
    def register_worker(self, workerName, **kwargs):
        address = ut.get_lan_ip()
        pid = os.getpid()
        self.produce('RegisterWorker', workerName, address=address, pid=pid, **kwargs)
    
    def update_worker(self, workerName, **kwargs):
        self.produce('UpdateWorker', workerName, **kwargs)

    def unregister_worker(self, workerName, **kwargs):
        self.produce('UnregisterWorker', workerName, **kwargs)

def print_help():
    print 'monkadmin.py -c <configFile> -m <maxNumWorkers>'

def main():
    global adminBroker, scheduler, maxNumWorkers
    configFile = 'monk_config.yml'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hc:m:',['configFile=', 'maxNumWorkers'])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ('-c', '--configFile'):
            configFile = arg
        elif opt in ('-m', '--maxNumWorkers'):
            maxNumWorkers = int(arg)
    
    config = Configuration(configFile, "administrator", str(os.getpid()))
    monkapi.initialize(config)
    adminBroker = AdminBroker(config.kafkaConnectionString, config.administratorGroup, config.administratorTopic, 
                              config.administratorServerPartitions, config.administratorClientPartitions)
    scheduler = mns.Scheduler('administrator-'+str(os.getpid()), [adminBroker])
    adminBroker.seek_to_end()
    scheduler.run()

if __name__=='__main__':
    main()