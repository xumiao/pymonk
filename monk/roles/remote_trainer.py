# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:45:09 2014
Training models remotely in cloud
@author: pacif_000
"""

import configuration
import logging
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import KeyedProducer
from ..core.api import initialize, add_data, train_one, load_one
import simplejson

config = configuration.Configuration("remote_trainer.yml")
initialize(config)
logger = logging.getLogger("monk.remote_trainer")
try:
    kafka = KafkaClient(config.kafkaConnectionString)
    producer = KeyedProducer(kafka, async=True)
    consumer = SimpleConsumer(kafka, config.kafkaGroup,
                              config.kafkaTopic,
                              partitions=[config.kafkaPartitionId])
    for message in consumer:
        decoded_message = simplejson.loads(message)
        user_id = decoded_message['userId']
        turtle_id = decoded_message['turtle_id']
        op = decoded_message['operation']        
        if op == 'add_data':
            entity = decoded_message['entity']
            fields = decoded_message['fields']
            add_data(turtle_id, user_id, entity, fields)
        elif op == 'train_one':
            train_one(turtle_id, user_id)
            producer.send(turtle_id, 0, simplejson.dumps({'userId':user_id}))
        elif op == 'load_one':
            load_one(turtle_id, user_id)
        else:
            logger.error('Operation not recognized {0}'.format(op))
            
except Exception as e:
    logger.warning('Exception {0}'.format(e))
    logger.warning('Can not consume actions')

kafka.close()