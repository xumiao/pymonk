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

turtleId = '53403a19e7f10034b8c89cea'
kafkaTopic = 'expression'
parts = range(1, 33)
users = {}

def add_data():
    global users
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')
        kafka = KafkaClient('mozo.cloudapp.net:9092', timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, parts, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)
        coll = mcl.DataSet['PMLExpression']

        for ent in coll.find(None, {'_id':True, 'userId':True}, timeout=False):
            entity = str(ent['_id'])
            userId = ent['userId']
            encodedMessage = simplejson.dumps({'turtleId':turtleId,
                                               'userId':userId,
                                               'entity':entity,
                                               'operation':'add_data'})
            print producer.send(userId, encodedMessage)
            
        for userId, partitionId in users.iteritems():
            encodedMessage = simplejson.dumps({'turtleId':turtleId,
                                               'userId':userId,
                                               'operation':'save_one'})
            print producer.send(userId, encodedMessage)
        userColl = mcl.DataSet['PMLUsers']
        if users:
            userColl.insert([{'userId':userId, 'partitionId':partitionId} for userId, partitionId in users.iteritems()])
    finally:
        producer.stop()
        mcl.close()
        kafka.close()

def train(numIters):
    global users
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')
        userColl = mcl.DataSet['PMLUsers']
        users = {user['userId']:user['partitionId'] for user in userColl.find()}
        mcl.close()
        kafka = KafkaClient('mozo.cloudapp.net:9092', timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)
        for i in range(numIters):
            num = 0
            for userId, partitionId in users.iteritems():
                if userId.find('.') >= 0:
                    continue
                num += 1
                if num == 10:
                    break
                encodedMessage = simplejson.dumps({'turtleId':turtleId,
                                                   'userId':userId,
                                                   'operation':'train_one'})
                print i, producer.send(userId, encodedMessage)
    finally:
        producer.stop()
        kafka.close()

    
if __name__=='__main__':
    add_data()
    #train(10)
