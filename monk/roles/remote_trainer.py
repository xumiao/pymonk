# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:45:09 2014
Training models remotely in cloud
@author: pacif_000
"""

from monk.core.configuration import Configuration
import monk.core.api as monkapi
import logging
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import KeyedProducer
from kafka.common import KafkaError
import simplejson
import sys, getopt
import os
import platform
import socket
if platform.system() == 'Windows':
    import win32api
else:
    import signal
import thread
import traceback

logger = logging.getLogger("monk.remote_trainer")

kafkaClient = None
producer = None
consumer = None

def print_help():
    print 'remote_trainer.py -c <configFile> -p <kafkaPartitions, e.g., range(1,8)>'
    
def onexit():
    closeKafka()
    monkapi.exits()
    logger.info('remote_rainter {0} is shutting down'.format(os.getpid()))

def handler(sig, hook = thread.interrupt_main):
    closeKafka()
    monkapi.exits()
    logger.info('remote_rainter {0} is shutting down'.format(os.getpid()))
    exit(1)

def initKafka(config, partitions):
    global kafkaClient, producer, consumer
    kafkaClient = KafkaClient(config.kafkaConnectionString)
    producer = KeyedProducer(kafkaClient, async=False,
                             req_acks=KeyedProducer.ACK_NOT_REQUIRED,
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
        
def server(configFile, partitions):
    global kafkaClient, producer, consumer
    config = Configuration(configFile, "remote_trainer", str(os.getpid()))
    monkapi.initialize(config)
    if platform.system() == 'Windows':
        win32api.SetConsoleCtrlHandler(handler, 1)
    else:
        signal.signal(signal.SIGINT, onexit)
    
    while True:
        try:
            closeKafka()
            initKafka(config, partitions)
            
            for message in consumer:
                logger.debug(message)
                decodedMessage = simplejson.loads(message.message.value)
                
                op         = decodedMessage.get('operation')
                user       = decodedMessage.get('user')
                turtleName = decodedMessage.get('turtleName')
                
                if user is None or turtleName is None:
                    logger.error('needs turtleId and userId')
                    continue
    
                if op == 'add_user':
                    follower = decodedMessage.get('follower')
                    if follower:
                        monkapi.clone_turtle(turtleName, user, follower)
                        monkapi.follow_turtle_leader(turtleName, user, follower)
                elif op == 'follow':
                    leader = decodedMessage.get('leader')
                    if leader:
                        monkapi.follow_turtle_follower(turtleName, user, leader)
                    follower = decodedMessage.get('follower')
                    if follower:
                        monkapi.follow_turtle_leader(turtleName, user, follower)
                elif op == 'unfollow':
                    leader = decodedMessage.get('leader')
                    if leader:
                        monkapi.unfollow_turtle_follower(turtleName, user, leader)
                    follower = decodedMessage.get('follower')
                    if follower:
                        monkapi.unfollow_turtle_leader(turtleName, user, follower)
                elif op == 'remove_user':
                    leader = monkapi.get_leader(turtleName, user)
                    monkapi.remove_turtle(turtleName, user)
                    encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                       'user':leader,
                                                       'follower':user,
                                                       'operation':'unfollow'})
                    producer.send(config.kafkaTopic, 8, encodedMessage)
                elif op == 'add_data':
                    entity = decodedMessage.get('entity')
                    if entity:
                        monkapi.add_data(turtleName, user, entity)
                elif op == 'save_turtle':
                    monkapi.save_turtle(turtleName, user) 
                elif op == 'merge':
                    follower = decodedMessage.get('follower')
                    iteration = decodedMessage.get('iteration', 0)
                    logger.debug('merging for interation {0}'.format(iteration))
                    if follower:
                        monkapi.merge(turtleName, user, follower)
                elif op == 'train':
                    iteration = decodedMessage.get('iteration',0)
                    logger.debug('training iteration {0}'.format(iteration))
                    monkapi.train(turtleName, user)
                    leader = monkapi.get_leader(turtleName, user)
                    encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                        'user':leader,
                                                        'follower':user,
                                                        'operation':'merge',
                                                        'iteration':iteration})
                    producer.send(config.kafkaTopic, 8, encodedMessage)
                elif op == 'test_data':
                    logger.debug('test on the data of {0}'.format(user))
                    entity = decodedMessage.get('entity')
                    #isPersonalized = decodedMessage.get('isPersonalized',1)
                    if entity:
                        monkapi.test_data(turtleName, user, entity)
                elif op == 'reset':
                    logger.debug('reset turtle {0} of user {1} '.format(turtleName, user))
                    monkapi.reset(turtleName, user)
                elif op == 'offsetCommit':
                    consumer.commit()
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

if __name__=='__main__':
    configFile = 'monk_config.yml'
    kafkaPartitions = [0]
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hc:p:',['configFile=', 'kafkaPartitions='])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ('-c', '--configFile'):
            configFile = arg
        elif opt in ('-p', '--kafkaPartitions'):
            kafkaPartitions = eval(arg)

    server(configFile, kafkaPartitions)
