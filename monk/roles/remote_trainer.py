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

def server(configFile, partitions):
    config = Configuration(configFile)
    if config.kafkaMasterPartition in partitions:
        print 'master is using partition {0}'.format(config.kafkaMasterPartition)
        return
    pid = os.getpid()
    fn = config.loggingConfig['handlers']['files']['filename']
    config.loggingConfig['handlers']['files']['filename'] = '.'.join([fn[:-4],'remote',str(pid),'log'])
    monkapi.initialize(config)
    
    try:
        kafka = KafkaClient(config.kafkaConnectionString,timeout=None)
        producer = KeyedProducer(kafka, async=False,
                                 req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE,
                                 ack_timeout=200)
        consumer = SimpleConsumer(kafka, config.kafkaGroup,
                                  config.kafkaTopic,
                                  partitions=partitions)
        for message in consumer:
            logger.debug(message)
            try:
                decodedMessage = simplejson.loads(message.message.value)
            except Exception as e:
                logger.error('Exception {0}'.format(e))
                logger.error('Message {0} is not in json format'.format(message.message.value))
                continue
            
            op = decodedMessage.get('operation')
            userId = decodedMessage.get('userId')
            turtleId = decodedMessage.get('turtleId')
            entity = decodedMessage.get('entity')
            if op == 'shutdown':
                logger.info('shutting down remote trainer server')
                break
            
            if userId is None or turtleId is None:
                logger.error('needs turtleId and userId')
                continue

            turtleId = monkapi.UUID(turtleId)
            if op == 'add_data':
                if 'entity' in decodedMessage:
                    entity = monkapi.UUID(decodedMessage['entity'])
                    monkapi.add_data(turtleId, userId, entity)
                else:
                    logger.error('add_data needs entity in string id')
            elif op == 'train_one':
                monkapi.train_one(turtleId, userId)
                encodedMessage = simplejson.dumps({'turtleId':str(turtleId),
                                                    'userId':userId, 
                                                    'operation':'aggregate'})
                producer.send(config.kafkaTopic, config.kafkaMasterPartition, encodedMessage)
            elif op == 'add_one':
                monkapi.add_one(turtleId, userId)
            elif op == 'load_one':
                monkapi.load_one(turtleId, userId)
            elif op == 'save_one':
                monkapi.save_one(turtleId, userId)
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
    configFile = 'remote_trainer.yml'
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
        elif opt in ('-p', '--kafkaPartition'):
            kafkaPartitions = eval(arg)

    server(configFile, kafkaPartitions)
