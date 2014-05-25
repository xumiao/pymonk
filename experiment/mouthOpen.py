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
from monk.math.flexible_vector import FlexibleVector
from random import sample
import numpy as np

logging.basicConfig(format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

turtleId = '53403a19e7f10034b8c89cea'
kafkaTopic = 'expression'
parts = range(1, 33)
users = {}
trainData = {}
testData = {}
UoI = {'Steve_70f97adb-2860-4b96-aff3-b538a1781581':int(0), 'Amanda_e824e832-d3de-4bbb-bc4d-f7774e02d3b5':int(0), 'carlos_fcfcb84e-3178-4c46-81ea-b8f8bb49709f':int(0)}
#UoI = {'carlos_fcfcb84e-3178-4c46-81ea-b8f8bb49709f':int(0), 'Amanda_e824e832-d3de-4bbb-bc4d-f7774e02d3b5':int(0)}
#UoI = {'Steve_70f97adb-2860-4b96-aff3-b538a1781581':int(0)}

def stop_add_data(userId):
    if UoI[userId] >= 10:
        return True
    else:
        return False
        
def add_data():
    global users
    global UoI
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
        
def addData():
    global users
    global UoI
    global trainData
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')
        kafka = KafkaClient('mozo.cloudapp.net:9092', timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, parts, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)        
        for userId in trainData.keys():            
            for ent in trainData[userId]:
                entity = str(ent)
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

def test(isPersonalized):
    global testData
    mcl = pm.MongoClient('10.137.168.196:27017')
    coll = mcl.DataSet['PMLExpression']
    MONKModelTurtleStore = mcl.MONKModel['TurtleStore']
    MONKModelPandaStore = mcl.MONKModel['PandaStore']
    #MONKModelMantisStore = mcl.MONKModel['MantisStore']
    turtle = MONKModelTurtleStore.find_one({'_id':ObjectId(turtleId)})
    pandas_id = turtle['pandas'][0]    
    panda = MONKModelPandaStore.find_one({'_id':pandas_id})
    pa = panda['weights']
    resGT = []  
    for user in testData.keys():
        #pa = MONKModelPandaStore.find({'userId': user}, {'_id':True, 'weights':True, 'consensus':True}, timeout=False)
        #[TODO] transform weights to FlexibleVector
        if isPersonalized == True:
            #field = 'weights.{0}'.format(user)
            #genericW = MONKModelPandaStore.load_one_in_fields(pa, [field])['weights'][user]
            wei = FlexibleVector(generic=pa[user])
        else:
            wei = FlexibleVector(generic=panda['consensus'])    
        for ent in coll.find({'_id': {'$in':testData[user]}}, {'_features':True, 'labels':True}, timeout=False):   
            #[TODO] transform features to FlexibleVector   
            fea = FlexibleVector(generic=ent['_features'])   
            if not len(ent['labels']) == 0:
                resGT.append((float(wei.dot(fea)), 1.0))
            else:
                resGT.append((float(wei.dot(fea)), 0.0))
    return resGT          
                
def retrieveData():
    mcl = pm.MongoClient('10.137.168.196:27017')        
    coll = mcl.DataSet['PMLExpression']
    originalData = {}
    for user in UoI.keys():
        originalData[user] = {'0':[], '1':[]}
    
    for ent in coll.find({'userId': {'$in': UoI.keys()}}, {'_id':True, 'userId':True, 'labels':True}, timeout=False):
        userId = ent['userId'] 
#        if (stop_add_data(userId)):
#            continue
#        UoI[userId] += 1
        if not len(ent['labels']) == 0:
            originalData[userId]['1'].append(ent['_id']) 
        else:
            originalData[userId]['0'].append(ent['_id'])             
        
    return originalData           
        
def splitData(originalData):
    global trainData
    global testData
    fracTrain = 0.5
    for user in originalData.keys():
        trainData[user] = []
        testData[user] = []
        numOfPosData = len(originalData[user]['1'])
        numOfNegData = len(originalData[user]['0'])
        pos = range(numOfPosData)
        neg = range(numOfNegData)
        selectedPos = stratifiedSelection(pos, fracTrain)
        selectedNeg = stratifiedSelection(neg, fracTrain)
        #selected = selectForTraining(numOfData, fracTrain)
        for i in range(numOfPosData):
            if i in selectedPos:
                trainData[user].append(originalData[user]['1'][i])                
            else:
                testData[user].append(originalData[user]['1'][i])
        for i in range(numOfNegData):
            if i in selectedNeg:
                trainData[user].append(originalData[user]['0'][i])                
            else:
                testData[user].append(originalData[user]['0'][i])          

def stratifiedSelection(index, fracTrain): 
    
    num = int(len(index)*fracTrain)
    selectIndex = sample(index, num)    
    
    return selectIndex
    
    
def evaluate(resGT, curvefile):
    totalP = 0.0
    totalN = 0.0
    for data in resGT:       
        if data[1] > 0:
           totalP += 1
        else:
           totalN += 1
    resGT.sort()    
    logging.debug("totalP = {0}".format(totalP))
    logging.debug("totalN = {0}".format(totalN))
    fCurve = file(curvefile, 'w')
    fCurve.write('threshold\tPrecision\tRecall\tFPrate\n')     
    totalFP = totalN
    totalFN = 0.0
    totalTP = totalP
    totalTN = 0.0   
    numberOfCurve = 500        
    minVal = float(resGT[0][0])
    maxVal = float(resGT[-1][0])
    thre = np.linspace(minVal, maxVal, numberOfCurve)
    k = 0
    for i in xrange(numberOfCurve):
        while(float(resGT[k][0]) < thre[i]):                
            if(float(resGT[k][1]) > 0):
                totalFN = totalFN + 1
            else:
                totalTN = totalTN + 1
            k = k + 1                    
        totalFP = totalN - totalTN
        totalTP = totalP - totalFN
            
        if(totalTP+totalFP == 0):
            precision = 1
        else:
            precision = float(totalTP) / float((totalTP+totalFP))                             
        if(totalP == 0):
            recall = 0
        else:
            recall = float(totalTP) / float(totalP)                             
        if(totalN == 0):
            FPrate = 0
        else:
            FPrate = float(totalFP) / float(totalN)       
        o = '{0:.8f}\t{1:.8f}\t{2:.8f}\t{3:.8f}'.format(thre[i], precision, recall, FPrate)            
        fCurve.write(o + '\n')
        
    fCurve.close()


           
if __name__=='__main__':
    ##### previous version; add data and train #####   
    remove_data_for_experiment_only()
    #add_data()
    #train(10)
    
    originalData = retrieveData()
    splitData(originalData)
    addData()
    train(10)
    isPersonalized= True
    resGT = test(isPersonalized)
    evaluate(resGT, "acc.curve")