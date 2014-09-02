# -*- coding: utf-8 -*-
"""
Created on Tue Apr 01 17:47:38 2014

@author: xumiao
"""

import pymongo as pm
from kafka.client import KafkaClient
from kafka.producer import UserProducer
import simplejson
import logging

logging.basicConfig(format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

turtleName = 'mouthOpenTurtle'
kafkaTopic = 'expr'
kafkaHost = 'monkkafka.cloudapp.net:9092'
partitions = range(8)
users = {}

def rebalance_users():
    for i in range(4):
        usersi = [user for user in users if users[user] == i]
        for user in usersi[len(usersi)/2:]:
            users[user] = i + 4
    
def add_users():
    global users
    
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')
        kafka = KafkaClient(kafkaHost, timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, partitions, async=False,
                                req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                                ack_timeout=200)
        coll = mcl.DataSet['PMLExpression']
        
        for ent in coll.find(None, {'_id':True, 'userId':True}, timeout=False):
            follower = ent['userId']
            if follower not in users:
                encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                   'user':'monk',
                                                   'follower':follower,
                                                   'operation':'add_user'})
                print producer.send(follower, encodedMessage)
        
        userColl = mcl.DataSet['PMLUsers']
        if users:
            userColl.insert([{'userId':userId, 'partitionId':partitionId} for userId, partitionId in users.iteritems()])
    finally:
        producer.stop()
        mcl.close()
        kafka.close()
        
def add_data():
    global users
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')
        kafka = KafkaClient(kafkaHost, timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, partitions, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)
        coll = mcl.DataSet['PMLExpression']

        for ent in coll.find(None, {'_id':True, 'userId':True}, timeout=False):
            entity = str(ent['_id'])
            user = ent['userId']
            encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                               'user':user,
                                               'entity':entity,
                                               'operation':'add_data'})
            print producer.send(user, encodedMessage)
            
        for user, partitionId in users.iteritems():
            encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                               'user':user,
                                               'operation':'save_turtle'})
            print producer.send(user, encodedMessage)
        mcl.close()
    finally:
        producer.stop()
        kafka.close()

def train(numIters):
    global users
    try:
        kafka = KafkaClient(kafkaHost, timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)
                          
        for i in range(numIters):
            for user, partitionId in users.iteritems():
                encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                   'user':user,
                                                   'operation':'train',
                                                   'iteration':i})
                print i, producer.send(user, encodedMessage)
    finally:
        producer.stop()
        kafka.close()

def test():
    global users
    pass

if __name__=='__main__':
    add_users()
    add_data()
    train(10)
