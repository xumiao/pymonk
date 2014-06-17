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
import simplejson
import sys, getopt
import os

logger = logging.getLogger("monk.remote_trainer")

def print_help():
    print 'remote_trainer.py -c <configFile> -p <kafkaPartitions, e.g., range(1,8)>'

def onexit():
    monkapi.exits()
    logger.info('remote_rainter {0} is shutting down'.format(os.getpid))
    
def server(configFile, partitions):
    config = Configuration(configFile, "remote_trainer", str(os.getpid()))
    monkapi.initialize(config)
    
    try:
        kafka = KafkaClient(config.kafkaConnectionString,timeout=None)
        producer = KeyedProducer(kafka, async=False,
                                 req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE,
                                 ack_timeout=200)
        consumer = SimpleConsumer(kafka, config.kafkaGroup,
                                  config.kafkaTopic,
                                  partitions=partitions)
        #consumer.seek(0, 2)                                       
        for message in consumer:
            logger.debug(message)
            try:
                decodedMessage = simplejson.loads(message.message.value)
            except Exception as e:
                logger.error('Exception {0}'.format(e))
                logger.error('Message {0} is not in json format'.format(message.message.value))
                continue
            
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
                producer.send(config.kafkaTopic, config.kafkaMasterPartition, encodedMessage)
            elif op == 'add_data':
                entity = decodedMessage.get('entity')
                if entity:
                    monkapi.add_data(turtleName, user, entity)
            elif op == 'save_turtle':
                monkapi.save_turtle(turtleName, user)
            elif op == 'merge':
                follower = decodedMessage.get('follower')
                if follower:
                    monkapi.merge(turtleName, user, follower)
            elif op == 'train':
                monkapi.train(turtleName, user)
                leader = monkapi.get_leader(turtleName, user)
                if not leader:
                    leader = user
                encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                    'user':leader,
                                                    'follower':user,
                                                    'operation':'merge'})
                producer.send(config.kafkaTopic, config.kafkaMasterPartition, encodedMessage)
            else:
                logger.error('Operation not recognized {0}'.format(op))
    except Exception as e:
        logger.warning('Exception {0}'.format(e))
        logger.warning('Can not consume actions')
    finally:
        consumer.commit()
        consumer.stop()
        producer.stop()
        kafka.close()
        monkapi.exits()
    
if __name__=='__main__':
    configFile = 'monk_config.yml'
    kafkaPartition = 1
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
