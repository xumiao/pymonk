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
from ..monk import initialize, add_data, train_one
import simplejson

config = configuration.Configuration("remote_trainer.yml")
initialize(config)
logger = logging.getLogger("monk")
turtle_id = config.kafkaTopic
try:
    kafka = KafkaClient(config.kafkaConnectionString)
    producer = KeyedProducer(kafka, async=True)
    consumer = SimpleConsumer(kafka, config.kafkaGroup,
                              config.kafkaTopic,
                              partitions=[config.kafkaPartitionId])
    for message in consumer:
        decoded_message = simplejson.loads(message)
        user_id = decoded_message['userId']
        if decoded_message['operation'] == 'add_data':
            entity = decoded_message['entity']
            fields = decoded_message['fields']
            add_data(turtle_id, user_id, entity, fields)
        elif decoded_message['operation'] == 'train_one':
            train_one(turtle_id, user_id)
            producer.send(turtle_id, 0, simplejson.dumps({'userId':user_id}))
except Exception as e:
    logger.warning('Exception {0}'.format(e))
    logger.warning('Can not consume actions')

kafka.close()