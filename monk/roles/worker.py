# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:45:09 2014
Training models remotely in cloud
@author: pacif_000
"""    
from monk.roles.configuration import get_config
from monk.roles.administrator import AdminBroker
from monk.roles.monitor import MonitorBroker
import monk.core.api as monkapi
import logging
import sys
from monk.network.broker import KafkaBroker
from monk.network.server import MonkServer, taskT, Task
import monk.utils.utils as ut

logger = logging.getLogger("monk.roles.worker")

class WorkerBroker(KafkaBroker):
    def add_clone(self, userName, turtleName, follower, **kwargs):
        self.producer.produce('AddClone', userName, turtleName=turtleName, follower=follower, **kwargs)
    
    def remove_clone(self, userName, turtleName, **kwargs):
        self.produce('RemoveClone', userName, turtleName=turtleName, **kwargs)
    
    def follow(self, userName, turtleName, leader=None, follower=None, **kwargs):
        self.produce('Follow', userName, turtleName=turtleName, leader=leader, follower=follower, **kwargs)
    
    def unfollow(self, userName, turtleName, leader=None, follower=None, **kwargs):
        self.produce('UnFollow', userName, turtleName=turtleName, leader=leader, follower=follower, **kwargs)
    
    def add_data(self, userName, turtleName, ent, **kwargs):
        self.produce('AddData', userName, turtleName=turtleName, entity=ent, **kwargs)
    
    def save_turtle(self, userName, turtleName, **kwargs):
        self.produce('SaveTurtle', userName, turtleName=turtleName, **kwargs)
    
    def merge(self, userName, turtleName, follower, **kwargs):
        self.produce('Merge', userName, turtleName=turtleName, follower=follower, **kwargs)
    
    def train(self, userName, turtleName, **kwargs):
        self.produce('Train', userName, turtleName=turtleName, **kwargs)

    def predict(self, userName, turtleName, ent, **kwargs):
        self.produce('Predict', userName, turtleNmae=turtleName, entity=ent, **kwargs)

    def reset(self, userName, turtleName, **kwargs):
        self.produce('Reset', userName, turtleName=turtleName, **kwargs)
    
    def reset_all_data(self, userName, turtleName, **kwargs):
        self.produce('ResetAllData', userName, turtleName=turtleName, **kwargs)
    
    def offset_commit(self, userName, turtleName, **kwargs):
        self.produce('OffsetCommit', userName, turtleName=turtleName, **kwargs)
    
    def set_mantis_parameter(self, userName, turtleName, para, value, **kwargs):
        self.produce('SetMantisParameter', userName, turtleName=turtleName, para=para, value=value, **kwargs)
    
    def monk_reload(self, **kwargs):
        self.produce('MonkReload', None, **kwargs)

class MonkWorker(MonkServer):
    def maintain(self):
        self.adminBroker.update_worker(self.serverName)
    
    def onexit(self):
        self.adminBroker.unregister_worker(self.serverName)
    
    def init_brokers(self, config):
        monkapi.initialize(config)
        self.adminBroker = AdminBroker(config.kafkaConnectionString, config.administratorGroup, config.administratorTopic, 
                                  config.administratorClientPartitions, config.administratorServerPartitions, producerType=KafkaBroker.FIXED_PRODUCER)
        self.workerBroker = WorkerBroker(config.kafkaConnectionString, config.workerGroup, config.workerTopic, producerType=KafkaBroker.USER_PRODUCER)
        self.monitorBroker = MonitorBroker(config.kafkaConnectionString, config.monitorGroup, config.monitorGroup, config.monitorTopic, 
                                       config.monitorClientPartitions, config.monitorServerPartitions, producerType=KafkaBroker.SIMPLE_PRODUCER)
        ut.set_monitor(self.monitorBroker)
        
        self.MAINTAIN_INTERVAL = config.workerMaintenanceInterval
        self.POLL_INTERVAL = config.workerPollInterval
        self.EXECUTE_INTERVAL = config.workerExecuteInterval
        self.MAX_QUEUE_SIZE = config.workerMaxQueueSize
        
        self.adminBroker.register_worker(self.serverName, offsetSkip=config.workerConsumerOffsetSkip)
        return [self.adminBroker, self.workerBroker, self.monitorBroker]
    
worker = MonkWorker()

@taskT
class WorkerTask(Task):
    def __init__(self, decodedMessage):
        self.decodedMessage = decodedMessage
        self.turtleName = decodedMessage.get('turtleName')
        self.userName = decodedMessage.get('name')

@taskT
class Train(WorkerTask):
    def act(self):
        monkapi.train(self.turtleName, self.userName)
        leader = monkapi.get_leader(self.turtleName, self.userName)
        worker.workerBroker.merge(leader, self.turtleName, self.userName)

@taskT
class Merge(WorkerTask):
    def act(self):
        follower = self.get('follower')
        if monkapi.merge(self.turtleName, self.userName, follower):
            for follower in monkapi.get_followers(self.turtleName, self.userName):
                worker.workerBroker.train(follower, self.turtleName)

@taskT
class Reset(WorkerTask):
    def act(self):
        logger.debug('reset turtle {} for user {}'.format(self.turtleName, self.userName))
        monkapi.reset(self.turtleName, self.userName)

@taskT
class SaveTurtle(WorkerTask):
    def act(self):
        monkapi.save_turtle(self.turtleName, self.userName)

@taskT
class ResetAllData(WorkerTask):
    def act(self):
        logger.debug('reset_all_data turtle {0} of user {1} '.format(self.turtleName, self.userName))
        monkapi.reset_all_data(self.turtleName, self.userName)

@taskT
class OffsetCommit(WorkerTask):
    def act(self):
        worker.workerBroker.commit()

@taskT
class SetMantisParameter(WorkerTask):
    def act(self):
        para = self.get('para', '')
        value = self.get('value', 0)
        logger.debug('set_mantis_parameter {} to {}'.format(para, value))
        monkapi.set_mantis_parameter(self.turtleName, self.userName, para, value)

@taskT        
class MonkReload(WorkerTask):
    def act(self):
        monkapi.reloads()

@taskT
class Follow(WorkerTask):
    def act(self):
        leader = self.get('leader')
        if leader:
            monkapi.follow_turtle_follower(self.turtleName, self.userName, leader)
        follower = self.get('follower')
        if follower:
            monkapi.follow_turtle_leader(self.turtleName, self.userName, follower)

@taskT
class UnFollow(WorkerTask):
    def act(self):
        leader = self.get('leader')
        if leader:
            monkapi.unfollow_turtle_follower(self.turtleName, self.userName, leader)
        follower = self.get('follower')
        if follower:
            monkapi.follow_turtle_leader(self.turtleName, self.userName, follower)

@taskT
class AddClone(WorkerTask):
    def act(self):
        follower = self.get('follower')
        if follower:
            monkapi.clone_turtle(self.turtleName, self.userName, follower)
            monkapi.follow_turtle_leader(self.turtleName, self.userName, follower)

@taskT
class RemoveClone(WorkerTask):
    def act(self):
        leader = monkapi.get_leader(self.turtleName, self.userName)
        followers = monkapi.get_followers(self.turtleName, self.userName)
        for follower in followers:
            worker.workerBroker.unfollow(follower, self.turtleName, leader=self.userName)
            worker.workerBroker.follow(follower, self.turtleName, leader=leader)
        monkapi.remove_turtle(self.turtleName, self.userName)
        worker.workerBroker.unfollow(leader, self.turtleName, follower=self.userName)

@taskT
class AddData(WorkerTask):
    def act(self):
        entity = self.get('entity')
        if entity:
            monkapi.add_data(self.turtleName, self.userName, entity)

@taskT
class Predict(WorkerTask):
    def act(self):
        logger.debug('test on data from {}'.format(self.userName))
        entity = self.get('entity')
        #isPersonalized = decodedMessage.get('isPersonalized',1)
        if entity:
            monkapi.predict(self.turtleName, self.userName, entity)

@taskT
class AcknowledgeRegistration(Task):
    def act(self):
        workerName = self.get('name')
        partition = self.get('partition')
        offsetSkip = self.get('offsetSkip')
        logger.info('Received registration for {} at partition {}'.format(workerName, partition))
        if workerName == worker.serverName:
            worker.workerBroker.set_consumer_partition([partition])
            logger.info('{} registered and is ready'.format(workerName))
            try:
                worker.workerBroker.seek(int(offsetSkip))
            except Exception as e:
                logger.warning('Can not seek to offset {}'.format(offsetSkip))
                logger.warning(e.message)

def main():
    global worker
    myname = '_'.join([sys.argv[1], ut.get_mac()])
    config = get_config(sys.argv[2:], myname, 'monkworker.py name')
    worker = MonkWorker(myname, config)
    worker.run()
    
if __name__=='__main__':
    main()
