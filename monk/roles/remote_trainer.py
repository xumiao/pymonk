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
from multiprocessing import Process

def print_help():
    print 'remote_trainer.py -c <configFile> -p <kafkaPartitions e.g. range(1,9)>'

def server(configFile, partition):
    config = Configuration(configFile)
    monkapi.initialize(config)
    logger = logging.getLogger("monk.remote_trainer")
    try:
        kafka = KafkaClient(config.kafkaConnectionString)
        producer = KeyedProducer(kafka, async=True)
        consumer = SimpleConsumer(kafka, config.kafkaGroup,
                                  config.kafkaTopic,
                                  partitions=[partition])
        for message in consumer:
            decodedMessage = simplejson.loads(message.message.value)
            userId = decodedMessage['userId']
            turtleId = monkapi.get_UUID(decodedMessage['turtleId'])
            op = decodedMessage['operation']
            if op == 'add_data':
                entity = monkapi.get_UUID(decodedMessage['entity'])
                monkapi.add_data(turtleId, userId, entity)
            elif op == 'train_one':
                monkapi.train_one(turtleId, userId)
                encodedMessage = simplejson.dumps({'turtleId':turtleId, 
                                                    'userId':userId, 
                                                    'operation':'aggregate'})
                producer.send(config.kafkaTopic, config.masterKafkaPartition, encodedMessage)
            elif op == 'add_one':
                monkapi.add_one(turtleId, userId)
            elif op == 'load_one':
                monkapi.load_one(turtleId, userId)
            else:
                logger.error('Operation not recognized {0}'.format(op))
    except Exception as e:
        logger.warning('Exception {0}'.format(e))
        logger.warning('Can not consume actions')
    finally:
        kafka.close()
        monkapi.exits()
    
if __name__=='__main__':
    configFile = 'remote_trainer.yml'
    kafkaPartitions = [1]
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
    
    ps = []
    for partition in kafkaPartitions:
        p = Process(target=server, args=(configFile, partition))
        ps.append(p)
        p.start()
    
    print len(kafkaPartitions), ' servers have been started'
    [p.join() for p in ps]