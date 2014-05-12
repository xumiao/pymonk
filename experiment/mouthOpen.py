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
from bson.objectid import ObjectId

logging.basicConfig(format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

turtleId = '53403a19e7f10034b8c89cea'
kafkaTopic = 'expression'
parts = range(1, 33)
users = {}
UoI = {'Steve_70f97adb-2860-4b96-aff3-b538a1781581':int(0), 'Amanda_e824e832-d3de-4bbb-bc4d-f7774e02d3b5':int(0), 'carlos_fcfcb84e-3178-4c46-81ea-b8f8bb49709f':int(0)}
#UoI = {'carlos_fcfcb84e-3178-4c46-81ea-b8f8bb49709f':int(0), 'Amanda_e824e832-d3de-4bbb-bc4d-f7774e02d3b5':int(0)}
UoI = {'carlos_fcfcb84e-3178-4c46-81ea-b8f8bb49709f':int(0), 'Amanda_e824e832-d3de-4bbb-bc4d-f7774e02d3b5':int(0)}
#UoI = {'Steve_70f97adb-2860-4b96-aff3-b538a1781581':int(0)}
def stop_add_data(userId):
    if UoI[userId] >= 10:
        return True
    else:
        return False
        
def add_data():
    global users
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')
        kafka = KafkaClient('mozo.cloudapp.net:9092', timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, parts, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)
        coll = mcl.DataSet['PMLExpression']
        ii = 0      # max is 151413 (number of doc in PMLExpression)
        for ent in coll.find({'userId': {'$in': UoI.keys()}}, {'_id':True, 'userId':True}, timeout=False):
            
            ii += 1
            entity = str(ent['_id'])
            userId = ent['userId']
            if (stop_add_data(userId)):
                continue
            UoI[userId] += 1
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
        for userId, partitionId in users.iteritems():   
            if userId in UoI.keys():    
                for i in range(numIters):                         
                    #print "iteration " + str(i)
                    encodedMessage = simplejson.dumps({'turtleId':turtleId,
                                                   'userId':userId,
                                                   'operation':'train_one'})
                    print i, producer.send(userId, encodedMessage)
    finally:
        producer.stop()
        kafka.close()

def remove_data_for_experiment_only():
    mcl = pm.MongoClient('10.137.168.196:27017')
    MONKModelTurtleStore = mcl.MONKModel['TurtleStore']
    MONKModelPandaStore = mcl.MONKModel['PandaStore']
    MONKModelMantisStore = mcl.MONKModel['MantisStore']
    MONKModelTigressStore = mcl.MONKModel['TigressStore']
    turtle = MONKModelTurtleStore.find_one({'_id':ObjectId(turtleId)})
    for pandas_id in turtle['pandas']:              # clean up pandas and mantis
        panda = MONKModelPandaStore.find_one({'_id':pandas_id})
        MONKModelPandaStore.update({'_id':pandas_id},{'$set':{'consensus':[]}})        
        MONKModelPandaStore.update({'_id':pandas_id},{'$set':{'weights':{}}})  
        MONKModelPandaStore.update({'_id':pandas_id},{'$set':{'local_consensus':{}}})  
        MONKModelPandaStore.update({'_id':pandas_id},{'$set':{'dual':{}}})  
        mantis_id = panda['mantis']
        MONKModelMantisStore.update({'_id':mantis_id},{'$set':{'data':{}}})     
    
    tigress_id = turtle['tigress']              # clean up tigress
    MONKModelTigressStore.update({'_id':tigress_id},{'$set':{'confusionMatrix':{}}})
        
        
if __name__=='__main__':
    remove_data_for_experiment_only()
    add_data()
    train(5)
