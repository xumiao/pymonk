# -*- coding: utf-8 -*-
"""
Created on Sun Oct  5 14:38:22 2014

@author: xm
"""

import logging
from kafka.client import KafkaClient
from kafka.producer import KeyedProducer
from kafka.consumer import SimpleConsumer
import traceback
import simplejson

logger = logging.getLogger('monk.roles.hub')

_kafkaHost   = None
_kafkaGroup  = None
_kafkaTopic  = None
_kafkaClient = None
_producer    = None
_consumer    = None
_partitions  = []

def initializeKafka(kafkaHost, kafkaGroup, kafkaTopic, partitions=None):
    global _kafkaHost, _kafkaGroup, _kafkaTopic, _kafkaClient, _producer, _consumer, _partitions
    _kafkaHost  = kafkaHost
    _kafkaGroup = kafkaGroup
    _kafkaTopic = kafkaTopic
    _partitions = partitions
    _kafkaClient = KafkaClient(_kafkaHost, timeout=None)
    _producer = KeyedProducer(_kafkaClient, async=False, req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, ack_timeout=200)
    _consumer = SimpleConsumer(_kafkaClient, _kafkaGroup, _kafkaTopic, partitions=_partitions)
            
def closeKafka():
    global _kafkaClient, _producer, _consumer
    if _consumer:
        _consumer.commit()
        _consumer.stop()
        _consumer = None
    if _producer:
        _producer.stop()
        _producer = None
    if _kafkaClient:
        _kafkaClient.close()
        _kafkaClient = None
    logger.info('Kafka connection closed')

def restartKafka():
    closeKafka()
    global _kafkaClient, _producer, _consumer
    _kafkaClient = KafkaClient(_kafkaHost, timeout=None)
    _producer = KeyedProducer(_kafkaClient, async=False, req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, ack_timeout=200)
    _consumer = SimpleConsumer(_kafkaClient, _kafkaGroup, _kafkaTopic, partitions=_partitions)
    logger.info('Kafka coonection restarted')

def seekToEnd():
    _consumer.seek(0,2)

def produce(**kwargs):
    try:
        partition = kwargs.get('partition', 0)
        encodedMessage = simplejson.dumps(dict(kwargs))
        _producer.send(_kafkaTopic, partition, encodedMessage)
    except Exception as e:
        logger.warning('Exception {}'.format(e))
        logger.debug(traceback.format_exec())
        restartKafka()
        
def consumeOne():
    try:
        message = _consumer.get_message()
        return message.message.value
    except Exception as e:
        logger.warning('Exception {}'.format(e))
        logger.debug(traceback.format_exc())
        restartKafka()
        
def consume(count=10):
    try:
        messages = _consumer.get_messages(count=count)
        return [message.message.value for message in messages]
    except Exception as e:
        logger.warning('Exception {}'.format(e))
        logger.debug(traceback.format_exc())
        restartKafka()
        