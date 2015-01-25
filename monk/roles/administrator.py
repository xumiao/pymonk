# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 18:24:30 2014

@author: xm
"""

from monk.roles.configuration import get_config
import monk.core.api as monkapi
import logging
from monk.network.broker import KafkaBroker
from monk.network.server import taskT, Task, MonkServer
from monk.roles.monitor import MonitorBroker
from monk.core.user import User
from monk.core.engine import Engine
import monk.core.constants as cons
import monk.utils.utils as ut
import sys,os
import datetime
from itertools import cycle

logger = logging.getLogger('monk.roles.administrator')

class AdminBroker(KafkaBroker):
    def acknowledge_registration(self, workerName, partition, offsetSkip, **kwargs):
        self.produce('AcknowledgeRegistration', workerName, partition=partition, offsetSkip=offsetSkip, **kwargs)
        
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


class MonkAdmin(MonkServer):
    def init_brokers(self, config):
        self.workers = {}
        monkapi.initialize(config)
        self.MAINTAIN_INTERVAL = config.administratorMaintainInterval
        self.POLL_INTERVAL = config.administratorPollInterval
        self.EXECUTE_INTERVAL = config.administratorExecuteInterval
        self.MAX_QUEUE_SIZE = config.administratorMaxQueueSize
        self.maxNumWorkers = config.administratorMaxNumWorkers
        self.adminBroker = AdminBroker(config.kafkaConnectionString,
                                       config.administratorGroup,
                                       config.administratorTopic,
                                       KafkaBroker.SIMPLE_CONSUMER,
                                       config.administratorServerPartitions,
                                       KafkaBroker.FIXED_PRODUCER,
                                       config.administratorClientPartitions)
        self.adminBroker.seek(config.administratorOffsetSkip)
        self.monitorBroker = MonitorBroker(config.kafkaConnectionString,
                                           config.monitorGroup,
                                           config.monitorTopic,
                                           producerType=KafkaBroker.FIXED_PRODUCER,
                                           producerPartitions=[0])
        ut.set_monitor(self.monitorBroker)
        return [self.adminBroker]

admin = MonkAdmin()

class AddUser(Task):
    def get_least_loaded_engine(self):
        if len(admin.workers) == 0:
            return None
        lengine = None
        lload = sys.maxint
        for engine in admin.workers.itervalues():
            if engine.is_active() and len(engine.users) < lload:
                lload = len(engine.users)
                lengine = engine
        return lengine
        
    def act(self):
        userName = self.get(User.NAME,'')
        if not userName:
            logger.error('empty user name {}'.format(self.decodedMessage))
            return
        user = monkapi.load_user(userName)
        if not user:
            leastLoadedEngine = self.get_least_loaded_engine()
            if leastLoadedEngine is None:
                logger.debug('no engine is active')
                return
            userScript = {User.NAME      : userName,\
                          User.CREATOR   : cons.DEFAULT_CREATOR,\
                          User.FPART     : leastLoadedEngine.partition,\
                          User.FFNAME    : self.get(User.FFNAME),\
                          User.FGENDER   : self.get(User.FGENDER),\
                          User.FLNAME    : self.get(User.FLNAME),\
                          User.FMName    : self.get(User.FMName),\
                          User.FPASSWORD : self.get(User.FPASSWORD),\
                          User.FYEAR     : int(self.get(User.FYEAR, '1900'))}
            user = monkapi.create_user(userScript)
            leastLoadedEngine.add_user(userName)
            logger.debug('{} add user {}'.format(leastLoadedEngine.name, leastLoadedEngine.users))
taskT(AddUser)

class DeleteUser(Task):
    def act(self):
        userName = self.get(User.NAME, '')
        if not userName or not monkapi.delete_user(userName):
            logger.info('trying to delete non-existant user {}'.format(userName))
        else:
            logger.debug('{} deleted'.format(userName))
taskT(DeleteUser)

class UpdateUser(Task):
    def act(self):
        userName = self.get(User.NAME, '')
        if not userName:
            logger.error('empty user name {}'.format(self.decodedMessage))
            return
        user = monkapi.load_user(userName)
        if not user:
            logger.error('user is not registered {}'.format(self.decodedMessage))
            return
        user._setattr(User.FFNAME,    self.get(User.FFNAME))
        user._setattr(User.FGENDER,   self.get(User.FGENDER))
        user._setattr(User.FLNAME,    self.get(User.FLNAME))
        user._setattr(User.FMName,    self.get(User.FMName))
        user._setattr(User.FPASSWORD, self.get(User.FPASSWORD))
        user._setattr(User.FPART,     self.get(User.FPART))
        user._setattr(User.FYEAR,     self.get(User.FYEAR), lambda x: int(x))
        user.save()
        logger.debug('{} updated'.format(user.generic()))
taskT(UpdateUser)

class RebalanceUsers(Task):
    def act(self):
        activeEngines = filter(lambda engine: engine.is_active(), admin.workers.itervalues())
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
taskT(RebalanceUsers)
    
class RegisterWorker(Task):
    def next_partition(self):
        if len(admin.workers) < admin.maxNumWorkers:
            return len(admin.workers)
        else:
            oldest = datetime.now()
            oldestWorker = None
            for worker in admin.workers:
                if worker.lastModified < oldest:
                    oldestWorker = worker
                    oldest = worker.lastModified
            return oldestWorker.partition
            
    def act(self):
        workerName = self.get(cons.BASE_NAME, '')
        if not workerName:
            logger.error('empty worker name {}'.format(self.decodedMessage))
            return
        logger.info('worker {} registering'.format(workerName))
        if workerName not in admin.workers:
            engine = monkapi.load_engine(workerName)
            if not engine:
                engineScript = {Engine.NAME: workerName,\
                                Engine.CREATOR: cons.DEFAULT_CREATOR,\
                                Engine.FPARTITION: self.next_partition(),\
                                Engine.FSTARTTIME: datetime.datetime.now(),\
                                Engine.FPID: self.get(Engine.FPID),\
                                Engine.FSTATUS: cons.STATUS_ACTIVE}
                logger.info('creating worker {}'.format(engineScript))
                engine = monkapi.create_engine(engineScript)
            admin.workers[workerName] = engine
        else:
            engine = admin.workers[workerName]
            engine._setattr(Engine.FSTARTTIME, datetime.datetime.now())
            engine._setattr(Engine.FSTATUS, cons.STATUS_ACTIVE)
            engine._setattr(Engine.FADDRESS, self.get(Engine.FADDRESS))
            engine._setattr(Engine.FPID,     self.get(Engine.FPID))
            engine.save()
        offsetSkip = self.get('offsetSkip', -1)
        admin.adminBroker.acknowledge_registration(workerName, engine.partition, offsetSkip)
taskT(RegisterWorker)

class UpdateWorker(Task):
    def act(self):
        workerName = self.get(Engine.NAME, '')
        if workerName not in admin.workers:
            engine = monkapi.load_engine(workerName)
            if not engine:
                logger.info('worker {} not registered'.format(workerName))
                return
            admin.workers[workerName] = engine
            logger.debug('workers {}'.format(admin.workers.keys()))
        else:
            engine = admin.workers[workerName]
        engine._setattr(Engine.FADDRESS, self.get(Engine.FADDRESS))
        engine._setattr(Engine.FPID,     self.get(Engine.FPID))
        engine._setattr(Engine.FSTATUS,  cons.STATUS_ACTIVE)
        engine.save()
taskT(UpdateWorker)

class UnregisterWorker(Task):
    def act(self):
        workerName = self.get('name', '')
        if not workerName:
            logger.error('empty worker name {}'.format(self.decodedMessage))
            return
        logger.info('worker {} unregistering'.format(workerName))
        if workerName in admin.workers:
            engine = admin.workers[workerName]
            engine._setattr(Engine.FSTATUS,  cons.STATUS_INACTIVE)
            engine._setattr(Engine.FENDTIME, datetime.datetime.now())
            engine.save()
taskT(UnregisterWorker)
        
def main():
    global admin
    myname = 'administrator'
    config = get_config(sys.argv[1:], myname, 'monkadmin.py')
    admin = MonkAdmin(myname, config)
    admin.run()

if __name__=='__main__':
    main()