# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 16:17:12 2014

@author: xm
"""

from monk.core.configuration import Configuration
import monk.core.api as monkapi
import pymongo as pm
import logging
import pymongo as pm
from kafka.client import KafkaClient
from kafka.producer import KeyedProducer
from kafka.consumer import SimpleConsumer
from kafka.common import KafkaError
import simplejson

kafkaClient = None
producer    = None
consumer    = None
userStore   = None
workerStore = None

def initializeKafka(config, partitions=None):
    global kafkaClient, producer, consumer
    kafkaClient = KafkaClient(config.kafkaHost, timeout=None)
    producer = KeyedProducer(kafkaClient, async=False, req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE, ack_timeout=200)
    if partitions:
        consumer = SimpleConsumer(kafkaClient, config.kafkaGroup, config.kafkaTopic, partitions=partitions)
            
def closeKafka():
    global kafkaClient, producer, consumer
    if consumer:
        consumer.commit()
        consumer.stop()
        consumer = None
    if producer:
        producer.stop()
        producer = None
    if kafkaClient:
        kafkaClient.close()
        kafkaClient = None

def initialize(config, partitions=None):
    global userStore, workerStore
    monkapi.initialize(config)
    userStore   = monkapi.crane.userStore
    workerStore = monkapi.crane.workerStore
    initializeKafka(config, partitions)
    
def exits():
    global userStore, workerStore
    userStore = None
    workerStore = None
    monkapi.exits()
    closeKafka()
    
def restartKafka(config, partitions=None):
    closeKafka()
    initializeKafka(config, partitions)
    
def add_user(userName, password=''):
    
    pass

def get_partition(userName, password=''):
    pass

def register_worker():
    pass

def update_worker():
    pass

def unregister_worker():
    pass

def add_data(turtleName, user, ent):
    pass

def reset(turtleName, user):
    pass

def train(turtleName, user):
    pass

def predict(turtleName, user, ent):
    pass

def add_follower(turtleName, user, follower):
    pass

