# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:45:09 2014
Training models remotely in cloud
@author: pacif_000
"""    
from monk.roles.configuration import Configuration
from monk.roles.administrator import AdminBroker
import monk.core.api as monkapi
import logging
import sys, getopt
import monk.network.broker as mnb
import monk.network.scheduler as mns
import monk.utils.utils as ut
import os

logger = logging.getLogger("monk.roles.worker")

adminBroker = None
workerBroker = None
scheduler = None

class WorkerTask(mnb.Task):
    def __init__(self, decodedMessage):
        self.decodedMessage = decodedMessage
        self.turtleName = decodedMessage.get('turtleName')
        self.userName = decodedMessage.get('name')

mnb.register(WorkerTask)
    
class Train(WorkerTask):
    def act(self):
        monkapi.train(self.turtleName, self.userName)
        leader = monkapi.get_leader(self.turtleName, self.userName)
        workerBroker.merge(leader, follower=self.userName, turtleName=self.turtleName)

mnb.register(Train)

class Merge(WorkerTask):
    def act(self):
        follower = self.decodedMessage.get('follower')
        if monkapi.merge(self.turtleName, self.userName, follower):
            for follower in monkapi.get_followers(self.turtleName, self.userName):
                workerBroker.train(follower, turtleName=self.turtleName)

mnb.register(Merge)

class Reset(WorkerTask):
    def act(self):
        logger.debug('reset turtle {} for user {}'.format(self.turtleName, self.userName))
        monkapi.reset(self.turtleName, self.userName)

mnb.register(Reset)

class SaveTurtle(WorkerTask):
    def act(self):
        monkapi.save_turtle(self.turtleName, self.userName)

mnb.register(SaveTurtle)

class ResetAllData(WorkerTask):
    def act(self):
        logger.debug('reset_all_data turtle {0} of user {1} '.format(self.turtleName, self.userName))
        monkapi.reset_all_data(self.turtleName, self.userName)

mnb.register(ResetAllData)

class OffsetCommit(WorkerTask):
    def act(self):
        workerBroker.commit()

mnb.register(OffsetCommit)

class SetMantisParameter(WorkerTask):
    def act(self):
        para = self.decodedMessage.get('para', '')
        value = self.decodedMessage.get('value', 0)
        logger.debug('set_mantis_parameter {} to {}'.format(para, value))
        monkapi.set_mantis_parameter(self.turtleName, self.userName, para, value)

mnb.register(SetMantisParameter)
        
class MonkReload(WorkerTask):
    def act(self):
        monkapi.reloads()

mnb.register(MonkReload)

class Follow(WorkerTask):
    def act(self):
        leader = self.decodedMessage.get('leader')
        if leader:
            monkapi.follow_turtle_follower(self.turtleName, self.userName, leader)
        follower = self.decodedMessage('follower')
        if follower:
            monkapi.follow_turtle_leader(self.turtleName, self.userName, follower)

mnb.register(Follow)

class UnFollow(WorkerTask):
    def act(self):
        leader = self.decodedMessage.get('leader')
        if leader:
            monkapi.unfollow_turtle_follower(self.turtleName, self.userName, leader)
        follower = self.decodedMessage('follower')
        if follower:
            monkapi.follow_turtle_leader(self.turtleName, self.userName, follower)

mnb.register(UnFollow)

class AddUser(WorkerTask):
    def act(self):
        follower = self.decodedMessage.get('follower')
        if follower:
            monkapi.clone_turtle(self.turtleName, self.userName, follower)
            monkapi.follow_turtle_leader(self.turtleName, self.userName, follower)

mnb.register(AddUser)
            
class RemoveUser(WorkerTask):
    def act(self):
        leader = monkapi.get_leader(self.turtleName, self.userName)
        monkapi.remove_turtle(self.turtleName, self.userName)
        workerBroker.unfollow(leader, turtleName=self.turtleName, follower=self.userName)

mnb.register(RemoveUser)

class AddData(WorkerTask):
    def act(self):
        entity = self.decodedMessage.get('entity')
        if entity:
            monkapi.add_data(self.turtleName, self.userName, entity)

mnb.register(AddData)

class TestData(WorkerTask):
    def act(self):
        logger.debug('test on data from {}'.format(self.userName))
        entity = self.decodedMessage.get('entity')
        #isPersonalized = decodedMessage.get('isPersonalized',1)
        if entity:
            monkapi.predict(self.turtleName, self.userName, entity)

mnb.register(TestData)

class AcknowledgeRegistration(mnb.Task):
    def act(self):
        workerName = self.decodedMessage.get('name')
        partition = self.decodedMessage.get('partition')
        offsetToEnd = self.decodedMessage.get('offsetToEnd')
        logger.info('Received registration for {} at partition {}'.format(workerName, partition))
        if workerName == ut.get_host_name():
            workerBroker.set_consumer_partition([partition])
            logger.info('{} registered and is ready'.format(workerName))
            if eval(offsetToEnd):
                workerBroker.seek_to_end()

mnb.register(AcknowledgeRegistration)
        
class WorkerBroker(mnb.KafkaBroker):
    def add_user(self, userName, turtleName, follower, **kwargs):
        self.producer.produce('AddUser', userName, turtleName=turtleName, follower=follower, **kwargs)
    
    def follow(self, userName, turtleName, leader, follower, **kwargs):
        if leader:
            self.produce('Follow', userName, turtleName=turtleName, leader=leader, **kwargs)
        if follower:
            self.produce('Follow', userName, turtleName=turtleName, follower=follower, **kwargs)
    
    def unfollow(self, userName, turtleName, leader, follower, **kwargs):
        if leader:
            self.produce('UnFollow', userName, turtleName=turtleName, leader=leader, **kwargs)
        if follower:
            self.produce('UnFollow', userName, turtleName=turtleName, follower=follower, **kwargs)
    
    def remove_user(self, userName, turtleName, **kwargs):
        self.produce('RemoveUser', userName, turtleName=turtleName, **kwargs)
    
    def add_data(self, userName, turtleName, ent, **kwargs):
        self.produce('AddData', userName, turtleName=turtleName, entity=ent, **kwargs)
    
    def save_turtle(self, userName, turtleName, **kwargs):
        self.produce('SaveTurtle', userName, turtleName=turtleName, **kwargs)
    
    def merge(self, userName, turtleName, follower, **kwargs):
        self.produce('Merge', userName, turtleName=turtleName, follower=follower, **kwargs)
    
    def train(self, userName, turtleName, **kwargs):
        self.produce('Train', userName, turtleName=turtleName, **kwargs)

    def test_data(self, userName, turtleName, ent, **kwargs):
        self.produce('TestData', userName, turtleNmae=turtleName, entity=ent, **kwargs)

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

def print_help():
    print 'monkworker.py -c <configFile> -o <to start from the last message>'

def main():
    configFile = 'monk_config.yml'
    global workerBroker, adminBroker, scheduler
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hoc:',['configFile='])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    offsetToEnd = False
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt == '-o':
            offsetToEnd = True
        elif opt in ('-c', '--configFile'):
            configFile = arg
    config = Configuration(configFile, "worker", str(os.getpid()))
    monkapi.initialize(config)
    adminBroker = AdminBroker(config.kafkaConnectionString, config.administratorGroup, config.administratorTopic, 
                              config.administratorClientPartitions, config.administratorServerPartitions)
    workerBroker = WorkerBroker(config.kafkaConnectionString, config.workerGroup, config.workerTopic)
    scheduler = mns.Scheduler('worker' + ut.get_host_name(), [adminBroker, workerBroker])
    #register this worker
    adminBroker.register_worker(offsetToEnd=offsetToEnd)
    scheduler.run()

if __name__=='__main__':
    main()
