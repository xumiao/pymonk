# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:45:09 2014
Training models remotely in cloud
@author: pacif_000
"""

from monk.core.configuration import Configuration
import monk.core.api as monkapi
import logging
import pymongo as pm
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import UserProducer
from kafka.common import KafkaError
import simplejson
import sys, getopt
import os
import platform
import monk.network.broker as mnb
import monk.utils.utils as ut

import socket
if platform.system() == 'Windows':
    import win32api
else:
    import signal
import thread
import traceback

logger = logging.getLogger("monk.worker")

kafkaClient = None
users = None
producer = None
consumer = None

class WorkerBroker(mnb.KafkaBroker):
    def add_data(turtleName, user, ent):
        pass
    
    def reset(turtleName, user):
        pass
    
    def train(turtleName, user):
        pass
    
    def predict(turtleName, user, ent):
        pass
    
    def add_follower(turtleName, user, follower):
        pass

class AdminBroker(mnb.KafkaBroker):
    def add_user(self, userName, password='', **kwargs):
        self.produce(partition=0, op='add_user', userName=userName, password=password, kwargs)
        
    def register_worker(self, **kwargs):
        produce(partition=0, op='register_worker', workerPID=os.getpgid(), workerIP=ut.get_lan_ip(), workerPartitions=self.partitions, kwargs)
    
    def update_worker(self, **kwargs):
        produce(partition=0, op='update_woorker', workerPID=os.getpgid(), workerIP=ut.get_lan_ip(), workerPartitions=self.partitions, kwargs)

    def unregister_worker(self, **kwargs):
        produce(partition=0, op='unregister_worker', workerPID=os.getpgid(), workerIP=ut.get_lan_ip(), workerPartitions=self.partitions, kwargs)


def print_help():
    print 'monkworker.py -c <configFile> -p <kafkaPartitions, e.g., range(1,8)> -o <to start from the last message'
    
def onexit():
    closeKafka()
    monkapi.exits()
    logger.info('worker {0} is shutting down'.format(os.getpid()))

def handler(sig, hook = thread.interrupt_main):
    closeKafka()
    monkapi.exits()
    logger.info('worker {0} is shutting down'.format(os.getpid()))
    exit(1)

def initKafka(config, partitions):
    global kafkaClient, producer, consumer, users
    kafkaClient = KafkaClient(config.kafkaConnectionString)
    users = {}
    mcl = pm.MongoClient('10.137.172.201:27017')
    userColl = mcl.DataSet['PMLUsers']
    allpartitions = set()
    for u in userColl.find(None, {'userId':True, 'partitionId':True}, timeout=False):
        users[u['userId']] = u['partitionId']
        allpartitions.add(u['partitionId'])
    mcl.close()
    logger.info('allpartitions = {0}'.format(allpartitions))
    producer = UserProducer(kafkaClient, config.kafkaTopic, users, list(allpartitions), async=False,
                            req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                            ack_timeout=200)
    consumer = SimpleConsumer(kafkaClient, config.kafkaGroup,
                              config.kafkaTopic,
                              partitions=partitions)

def closeKafka():
    global kafkaClient, producer, consumer
    if consumer:
        consumer.commit()
        consumer.stop()
        consumer = None
    if producer:
        producer.stop()
        producer = None
    if kafkaClient:
        kafkaClient.close()
        kafkaClient = None
        
def server(configFile, partitions, ote):
    global kafkaClient, producer, consumer
    config = Configuration(configFile, "worker", str(os.getpid()))
    monkapi.initialize(config)
    if platform.system() == 'Windows':
        win32api.SetConsoleCtrlHandler(handler, 1)
    else:
        signal.signal(signal.SIGINT, onexit)
    
    while True:
        try:
            closeKafka()
            initKafka(config, partitions)
            if ote:
                consumer.seek(0,2)
                logger.info('offset to end')
                ote = False
                
            for message in consumer:
                logger.debug(message)
                decodedMessage = simplejson.loads(message.message.value)
                
                op         = decodedMessage.get('operation')
                userName   = decodedMessage.get('userName')
                turtleName = decodedMessage.get('turtleName')
                
                if userName is None or turtleName is None:
                    logger.error('needs turtleId and userId')
                    continue
    
                if op == 'add_user':
                    follower = decodedMessage.get('follower')
                    if follower:
                        monkapi.clone_turtle(turtleName, userName, follower)
                        monkapi.follow_turtle_leader(turtleName, userName, follower)
                elif op == 'follow':
                    leader = decodedMessage.get('leader')
                    if leader:
                        monkapi.follow_turtle_follower(turtleName, userName, leader)
                    follower = decodedMessage.get('follower')
                    if follower:
                        monkapi.follow_turtle_leader(turtleName, userName, follower)
                elif op == 'unfollow':
                    leader = decodedMessage.get('leader')
                    if leader:
                        monkapi.unfollow_turtle_follower(turtleName, userName, leader)
                    follower = decodedMessage.get('follower')
                    if follower:
                        monkapi.unfollow_turtle_leader(turtleName, userName, follower)
                elif op == 'remove_user':
                    leader = monkapi.get_leader(turtleName, userName)
                    monkapi.remove_turtle(turtleName, userName)
                    encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                       'user':leader,
                                                       'follower':userName,
                                                       'operation':'unfollow'})
                    producer.send(leader, encodedMessage)
                elif op == 'add_data':
                    entity = decodedMessage.get('entity')
                    if entity:
                        monkapi.add_data(turtleName, userName, entity)
                elif op == 'save_turtle':
                    monkapi.save_turtle(turtleName, userName) 
                elif op == 'merge':
                    follower = decodedMessage.get('follower')
                    if (monkapi.merge(turtleName, userName, follower)):
                        for follower in monkapi.get_followers(turtleName, userName):
                            encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                               'user':follower,
                                                               'operation':'train'})
                            producer.send(follower, encodedMessage)
                elif op == 'train':
                    monkapi.train(turtleName, userName)
                    leader = monkapi.get_leader(turtleName, userName)
                    encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                        'user':leader,
                                                        'follower':userName,
                                                        'operation':'merge'})
                    producer.send(leader, encodedMessage)
                elif op == 'test_data':
                    logger.debug('test on the data of {0}'.format(userName))
                    entity = decodedMessage.get('entity')
                    #isPersonalized = decodedMessage.get('isPersonalized',1)
                    if entity:
                        monkapi.predict(turtleName, userName, entity)
                elif op == 'reset':
                    logger.debug('reset turtle {0} of user {1} '.format(turtleName, userName))
                    monkapi.reset(turtleName, userName)
                elif op == 'reset_all_data':
                    logger.debug('reset_all_data turtle {0} of user {1} '.format(turtleName, userName))
                    monkapi.reset_all_data(turtleName, userName)    
                elif op == 'offsetCommit':
                    consumer.commit()
                elif op == 'set_mantis_parameter':
                    para = decodedMessage.get('para', '')
                    value = decodedMessage.get('value', 0)
                    logger.debug('set_mantis_parameter {0} to {1}'.format(para, value))
                    monkapi.set_mantis_parameter(turtleName, userName, para, value)
                elif op == 'reload':
                    monkapi.reloads()
                else:
                    logger.error('Operation not recognized {0}'.format(op))
        except simplejson.JSONDecodeError as e:
            logger.warning('Exception message is not in Json format {0}'.format(e))
        except socket.error as e:
            logger.warning('Exception network error {0}'.format(e))
        except KafkaError as e :
            logger.warning('Exception from Kafka {0}'.format(e))
        except Exception as e:
            logger.warning('Exception {0}'.format(e))
        except KeyboardInterrupt:
            onexit()
            
        logger.debug(traceback.format_exc())
        logger.warning('Restart Kafka....\n')

def main():
    configFile = 'monk_config.yml'
    kafkaPartitions = [0]
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hoc:p:',['configFile=', 'kafkaPartitions='])
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
        elif opt in ('-p', '--kafkaPartitions'):
            kafkaPartitions = eval(arg)

    server(configFile, kafkaPartitions, offsetToEnd)
    
if __name__=='__main__':
    main()