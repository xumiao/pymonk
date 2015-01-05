# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 16:17:12 2014

@author: xm
"""

import logging
from kafka.client import KafkaClient
from kafka.producer.keyed import KeyedProducer
from producer import FixedProducer
from kafka.producer import SimpleProducer
from kafka.consumer.simple import SimpleConsumer
from kafka.common import KafkaError
from partitioner import UserPartitioner
import simplejson
import traceback

logger = logging.getLogger('monk.network.broker')

class KafkaBroker(object):
    USER_PRODUCER = 0
    FIXED_PRODUCER = 1
    SIMPLE_PRODUCER = 2
    NON_PRODUCER = 3
    SIMPLE_CONSUMER = 0
    NON_CONSUMER = 1
    
    def __init__(self, kafkaHost=None, kafkaGroup=None, kafkaTopic=None, 
                 consumerType=NON_CONSUMER, consumerPartitions=[],
                 producerType=NON_PRODUCER, producerPartitions=[]):
        self.kafkaHost = kafkaHost
        self.kafkaGroup = kafkaGroup
        self.kafkaTopic = kafkaTopic
        self.consumerPartitions = consumerPartitions
        self.producerPartitions = producerPartitions
        self.kafkaClient = KafkaClient(kafkaHost)
        try:
            if producerType == self.SIMPLE_PRODUCER:
                self.producer = SimpleProducer(self.kafkaClient, async=False, req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, ack_timeout=200)
            elif producerType == self.FIXED_PRODUCER:
                self.producer = FixedProducer(self.kafkaClient, producerPartitions[0], async=False, ack_timeout=200)
            elif producerType == self.USER_PRODUCER:
                self.producer = KeyedProducer(self.kafkaClient, partitioner=UserPartitioner, async=False,
                                          req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, ack_timeout=200)
            elif producerType == self.NON_PRODUCER:
                self.producer = None
            else:
                raise Exception("wrong producer type {}".format(producerType))
            
            if consumerType == self.SIMPLE_CONSUMER:
                if not consumerPartitions:
                    self.consumer = SimpleConsumer(self.kafkaClient, self.kafkaGroup, self.kafkaTopic)
                else:
                    self.consumer = SimpleConsumer(self.kafkaClient, self.kafkaGroup, 
                                                   self.kafkaTopic, partitions=self.consumerPartitions)
                logger.debug('consumer is listening on {}@{}'.format(self.kafkaTopic, self.consumerPartitions))
            elif consumerType == self.NON_CONSUMER:
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
            self.kafkaClient.reinit()
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
            self.kafkaClient.reinit()
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
    
    def is_consumer_ready(self):
        if not self.consumer:
            logger.warning('Consumer is not ready yet')
            return False
        return True
        
    def seek(self, skip):
        if self.is_consumer_ready():
            if skip == -1:
                self.consumer.seek(0,2)
            else:
                self.consumer.seek(skip, 1)
            
    def commit(self):
        if self.is_consumer_ready():
            self.consumer.commit()
            
    def consume_one(self):
        if not self.is_consumer_ready():
            return None
            
        try:
            message = self.consumer.get_message()
            if not message:
                return None
            return message.message.value
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.kafkaClient.reinit()
        return None
        
    def consume(self, count=10):
        if not self.is_consumer_ready():
            return []
            
        try:
            messages = self.consumer.get_messages(count=count)
            return [message.message.value for message in messages]
        except Exception as e:
            logger.warning('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            self.kafkaClient.reinit()
        return []
