# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:46:02 2014
Aggregate individual models periodically
@author: pacif_000
"""
from monk.core.configuration import Configuration
import monk.core.api as monkapi
import logging
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
import simplejson
import sys, getopt

logger = logging.getLogger("monk.master")

def print_help():
    print 'master.py -c <configFile>'
    
def main(argv):
    configFile = 'master.yml'
    
    try:
        opts, args = getopt.getopt(argv, 'hc:',['configFile='])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ('-c', '--configFile'):
            configFile = arg
    
    config = Configuration(configFile)
    monkapi.initialize(config)
        
    try:
        kafka = KafkaClient(config.kafkaConnectionString)
        consumer = SimpleConsumer(kafka, config.kafkaGroup,
                                  config.kafkaTopic,
                                  partitions=[config.kafkaMasterPartition])
        for message in consumer:
            logger.debug(message)
            decodedMessage = simplejson.loads(message.message.value)
            op = decodedMessage['operation']
            if op == 'aggregate':
                turtleId = monkapi.UUID(decodedMessage['turtleId'])
                userId = decodedMessage['userId']
                monkapi.aggregate(turtleId, userId)
            elif op == 'create':
                turtleScript = decodedMessage['turtleScript']
                turtleId = monkapi.find_turtle(turtleScript)
                monkapi.save_turtle(turtleId)
            else:
                logger.error('Operation unrecognizable {0}'.format(op))
    except Exception as e:
        logger.warning('Exception {0}'.format(e.message))
        logger.warning('Can not consume messages')
    finally:
        kafka.close()
        monkapi.exits()
    
if __name__=='__main__':
    main(sys.argv[1:])