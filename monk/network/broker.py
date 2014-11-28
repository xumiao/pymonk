# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 16:17:12 2014

@author: xm
"""

import logging
from kafka.client import KafkaClient
from kafka.producer.keyed import KeyedProducer
from producer import FixedProducer
from kafka.consumer.simple import SimpleConsumer
from kafka.common import KafkaError
from partitioner import UserPartitioner
import simplejson
import traceback

logger = logging.getLogger('monk.network.broker')

class TaskFactory(object):

    def __init__(self):
        self.factory = {}

    def register(self, TaskClass):
        className = TaskClass.__name__
        if className not in self.factory:
            self.factory[TaskClass.__name__] = TaskClass

    def find(self, name):
        return [key for key in self.factory.iterkeys() if key.find(name) >= 0]
        
    def create(self, message):
        try:
            logger.debug('Task from message {}'.format(message))
            generic = simplejson.loads(message)
            name = generic.get('op', None)
            if not name:
                return None
            else:
                return self.factory[name](generic)
        except Exception as e:
            logger.debug('can not create tasks for {}'.format(message))
            logger.debug('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            return None

brokerTaskFactory = TaskFactory()

def register(TaskClass):
    brokerTaskFactory.register(TaskClass)

class Task(object):
    PRIORITY_HIGH = 1
    PRIORITY_LOW = 5
    
    def __init__(self, decodedMessage):
        self.decodedMessage = decodedMessage
        self.priority = int(decodedMessage.get('priority', Task.PRIORITY_LOW))
    
    def act(self):
        logger.warning('no task is defined for {}'.format(self.decodedMessage))
    
register(Task)

class KafkaBroker(object):
    
    def __init__(self, kafkaHost, kafkaGroup, kafkaTopic, consumerPartitions=[], producerPartitions=[]):
        self.kafkaHost = kafkaHost
        self.kafkaGroup = kafkaGroup
        self.kafkaTopic = kafkaTopic
        self.consumerPartitions = consumerPartitions
        self.producerPartitions = producerPartitions
        self.kafkaClient = KafkaClient(kafkaHost, timeout=None)
        try:
            if self.producerPartitions:
                self.producer = FixedProducer(self.kafkaClient, producerPartitions[0], async=False, ack_timeout=200)
            else:
                self.producer = KeyedProducer(self.kafkaClient, partitioner=UserPartitioner, async=False,
                                          req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, ack_timeout=200)
            if consumerPartitions:
                self.consumer = SimpleConsumer(self.kafkaClient, self.kafkaGroup, 
                                               self.kafkaTopic, partitions=self.consumerPartitions)
                logger.debug('consumer is listening on {}@{}'.format(self.kafkaTopic, self.consumerPartitions))
            else:
                self.consumer = None
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
        if self.producerPartitions:
            self.producer = FixedProducer(self.kafkaClient, self.producerPartitions[0], async=False, ack_timeout=200)
        else:
            self.producer = KeyedProducer(self.kafkaClient, partitioner=UserPartitioner, async=False,
                                      req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, ack_timeout=200)
        if self.consumerPartitions:
            self.consumer = SimpleConsumer(self.kafkaClient, self.kafkaGroup, 
                                           self.kafkaTopic, partitions=self.consumerPartitions)
            logger.debug('consumer is listening on {}@{}'.format(self.kafkaTopic, self.consumerPartitions))
        else:
            self.consumer = None
                                       
        logger.info('Kafka coonection restarted')

    def produce(self, op, name, **kwargs):
        # TODO: when name is None, the operation is propagated to all partitions 
        if not op or not name:
            logger.warning('op or name must not be empty')
            return
            
        try:
            dictMessage = dict(kwargs)
            dictMessage['op'] = op
            dictMessage['name'] = name
            encodedMessage = simplejson.dumps(dictMessage)
            self.producer.send(self.kafkaTopic, name, encodedMessage)
        except KafkaError as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.reconnect()
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())

    def set_consumer_partition(self, consumerPartitions):
        if not consumerPartitions:
            logger.warning('consumer partitions can not be empty')
            return
            
        if self.consumer:
            self.consumer.commit()
            self.consumer.stop()
            self.consumer = None
        self.consumerPartitions = consumerPartitions
        try:
            self.consumer = SimpleConsumer(self.kafkaClient, self.kafkaGroup,
                                           self.kafkaTopic, partitions=self.consumerPartitions)
        except KafkaError as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.reconnect()
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
    
    def is_consumer_ready(self):
        if not self.consumer:
            logger.warning('Consumer is not ready yet')
            return False
        return True
        
    def seek_to_end(self):
        if self.is_consumer_ready():
            self.consumer.seek(0,2)
        
    def commit(self):
        if self.is_consumer_ready():
            self.consumer.commit()
            
    def consumeOne(self):
        if not self.is_consumer_ready():
            return None
            
        try:
            message = self.consumer.get_message()
            if not message:
                return None
            return brokerTaskFactory.create(message.message.value)
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.reconnect()
        return None
        
    def consume(self, count=10):
        if not self.is_consumer_ready():
            return []
            
        try:
            messages = self.consumer.get_messages(count=count)
            return [brokerTaskFactory.create(message.message.value) for message in messages]
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.reconnect()
        return []
