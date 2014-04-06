# -*- coding: utf-8 -*-
"""
Created on Sat Mar 15 12:06:30 2014

@author: xm
"""

from kafka.client import KafkaClient
from kafka.producer import KeyedProducer
from kafka.partitioner import HashedPartitioner, RoundRobinPartitioner

kafka = KafkaClient("mozo.cloudapp.net:9092")

# HashedPartitioner is default
producer = KeyedProducer(kafka)
producer.send("test", "key1", "some message")
producer.send("test", "key2", "this methode")
kafka.close()