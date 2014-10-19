# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 16:17:12 2014

@author: xm
"""

import logging
from kafka.client import KafkaClient
from kafka.producer import KeyedProducer
from kafka.consumer import SimpleConsumer
from kafka.common import KafkaError
import simplejson
import traceback

logger = logging.getLogger('monk.roles.broker')

class Task(object):
    PRIORITY_HIGH = 1
    PRIORITY_LOW = 5
    priority = 5
    
    def __init__(self, decodedMessage):
        self.decodedMessage = decodedMessage
    
    def act(self):
        logger.warning('no task is defined for {}'.format(self.decodedMessage))
    
    @classmethod
    def create(cls, message):
        decodedMessage = simplejson.loads(message)
        op = decodedMessage.get('op', None)
        try:
            task = eval(op)(decodedMessage)
            return (task.priority, task)
        except:
            return (Task.PRIORITY_LOW, None)
            
class KafkaBroker(object):
    def __init__(self, kafkaHost, kafkaGroup, kafkaTopic, partitions):
        self.kafkaHost = kafkaHost
        self.kafkaGroup = kafkaGroup
        self.kafkaTopic = kafkaTopic
        self.partitions = partitions
        self.kafkaClient = KafkaClient(kafkaHost, timeout=None)
        try:
            self.producer = KeyedProducer(self.kafkaClient, async=False, 
                                          req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, 
                                          ack_timeout=200)
            self.consumer = SimpleConsumer(self.kafkaClient, self.kafkaGroup, 
                                           self.kafkaTopic, partitions=self.partitions)
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.consumer = None
            self.producer = None
            self.kafkaClient = None
            
    def close(self):
        if self.consumer:
            self.consumer.commit()
            self.consumer.stop()
            self.consumer = None
        if self.producer:
            self.producer.stop()
            self.producer = None
        if self.kafkaClient:
            self.kafkaClient.close()
            self.kafkaClient = None
        logger.info('Kafka connection closed')
    
    def reconnect(self):
        self.close()
        self.kafkaClient = KafkaClient(self.kafkaHost, timeout=None)
        self.producer = KeyedProducer(self.kafkaClient, async=False, 
                                      req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, 
                                      ack_timeout=200)
        self.consumer = SimpleConsumer(self.kafkaClient, self.kafkaGroup, 
                                       self.kafkaTopic, partitions=self.partitions)
                                       
        logger.info('Kafka coonection restarted')

    def produce(self, partition, **kwargs):
        try:
            encodedMessage = simplejson.dumps(dict(kwargs))
            self.producer.send(self.kafkaTopic, partition, encodedMessage)
        except KafkaError as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exec())
            self.reconnect()
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
        
    def seekToEnd(self):
        self.consumer.seek(0,2)
        
    def consumeOne(self):
        try:
            message = self.consumer.get_message()
            return Task.create(message.message.value)
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.reconnect()
        
    def consume(self, count=10):
        try:
            messages = self.consumer.get_messages(count=count)
            return [Task.create(message.message.value) for message in messages]
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.reconnect()
    
