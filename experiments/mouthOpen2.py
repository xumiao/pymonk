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
from monk.math.flexible_vector import FlexibleVector
from random import sample
import pickle
import numpy as np
import matplotlib.pyplot as plt

logging.basicConfig(format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

turtleName = 'mouthOpenTurtle2'
pandaName = 'mouthOpen2'
kafkaTopic = 'expr'
partitions = range(8)
users = {}
trainData = {}          # the ObjectID of the selected data in DB
testData = {}
UoI = {}
fracTrain = 0.5

def rebalance_users():
    for i in range(4):
        usersi = [user for user in users if users[user] == i]
        for user in usersi[len(usersi)/2:]:
            users[user] = i + 4

def prepareData():
    global trainData    
    global testData
    originalData = retrieveData()
    splitData(originalData)
    
    destfile = open("trainData", 'w')       # save trainData _id
    pickle.dump(trainData, destfile)
    destfile.close()
    
    destfile = open("testData", 'w')       # save testData _id
    pickle.dump(testData, destfile)
    destfile.close()

def loadPreparedData(file1, file2 = None):
    global trainData    
    global testData
    
    destfile = open(file1, 'r')       # load trainData _id
    trainData = pickle.load(destfile)
    destfile.close()
    
    if(file2):
        destfile = open(file2, 'r')       # load testData _id
        testData = pickle.load(destfile)
        destfile.close()
        
def add_users():
    global users
    
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')
        kafka = KafkaClient('mozo.cloudapp.net:9092', timeout=None)
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
            for userId, partitionId in users.iteritems():            
                u = userColl.find_one({'userId':userId}, {'userId':userId}, timeout=False)
                if not u:
                    userColl.insert({'userId':userId, 'partitionId':partitionId});
            #userColl.insert([{'userId':userId, 'partitionId':partitionId} for userId, partitionId in users.iteritems()])
    finally:
        producer.stop()
        mcl.close()
        kafka.close()
        
def add_data():
    global users
    global trainData
    checkUserPartitionMapping()
    try:
        mcl = pm.MongoClient('10.137.168.196:27017')        
        kafka = KafkaClient('mozo.cloudapp.net:9092', timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, partitions, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)
        coll = mcl.DataSet['PMLExpression']

        for ent in coll.find(None, {'_id':True, 'userId':True}, timeout=False):
            entity = str(ent['_id'])
            user = ent['userId']
            if ent['_id'] in trainData[user]:
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
    checkUserPartitionMapping()
    try:
        kafka = KafkaClient('mozo.cloudapp.net:9092', timeout=None)
        producer = UserProducer(kafka, kafkaTopic, users, async=False,
                          req_acks=UserProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=200)
        for i in range(numIters):
            for user, partitionId in users.iteritems():
                encodedMessage = simplejson.dumps({'turtleName':turtleName,
                                                   'user':user,
                                                   'operation':'train'})
                print i, producer.send(user, encodedMessage)
    finally:
        producer.stop()
        kafka.close()

def test(isPersonalized):
    global users
    global testData
    checkUserPartitionMapping
    
    mcl = pm.MongoClient('10.137.168.196:27017')
    coll = mcl.DataSet['PMLExpression']
    #MONKModelTurtleStore = mcl.MONKModel['TurtleStore']
    MONKModelPandaStore = mcl.MONKModel['PandaStore']
    #MONKModelMantisStore = mcl.MONKModel['MantisStore']
    monkpa = MONKModelPandaStore.find_one({'creator': 'monk', 'name': pandaName}, {'_id':True, 'weights':True, 'z':True}, timeout=False)
    resGT = []  
    for user in testData.keys():
#        if user == '':
#            continue
        pa = MONKModelPandaStore.find_one({'creator': user, 'name': pandaName}, {'_id':True, 'weights':True, 'z':True}, timeout=False)
        if pa == None:
            continue
        if isPersonalized == True:
            #field = 'weights.{0}'.format(user)
            #genericW = MONKModelPandaStore.load_one_in_fields(pa, [field])['weights'][user]
            wei = FlexibleVector(generic=pa['weights'])
        else:
            #wei = FlexibleVector(generic=pa['z'])
            wei = FlexibleVector(generic=monkpa['z'])
        for ent in coll.find({'_id': {'$in':testData[user]}}, {'_features':True, 'labels':True}, timeout=False):     
            fea = FlexibleVector(generic=ent['_features'])   
            if not len(ent['labels']) == 0:
                resGT.append((float(wei.dot(fea)), 1.0))
            else:
                resGT.append((float(wei.dot(fea)), 0.0))
    return resGT              

def evaluate(resGT, curvefile):
    totalP = 0.0
    totalN = 0.0
    for data in resGT:            # remove the wrong values
        if data[0] > 100000:
           resGT.remove(data)
        elif data[0] < -100000:
           resGT.remove(data)
    for data in resGT:       
        if data[1] > 0:
           totalP += 1
        else:
           totalN += 1
    resGT.sort()    
    logging.debug("totalP = {0}".format(totalP))
    logging.debug("totalN = {0}".format(totalN))
    fCurve = open(curvefile, 'w')
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
            
def plotCurve(fileNames):
    
    groupTH = []
    groupTP = []
    groupFP = []
    groupPrecision = []
    
    for fileName in fileNames:
        f = file(fileName, 'r')
        
        th = []    
        precision = []
        recall = []
        fpRate = []
        
        i = 0
        f.readline()
        
        strs = f.readline().split('\t')
        while (len(strs) != 0 and strs[0] != ''):
            i+=1
            if(i== 500):
                print "cool"
            th.append(float(strs[0]))
            precision.append(float(strs[1]))
            recall.append(float(strs[2]))
            fpRate.append(float(strs[3]))
            strs = f.readline().split('\t')
        groupTH.append(th)
        groupTP.append(recall)
        groupFP.append(fpRate)   
        groupPrecision.append(precision)   
        f.close()
        
    
    #print '{0}\t{1}\t{2}\t{3}'.format(float(th[-1]), float(precision[-1]), float(recall[-1]), float(fpRate[-1]))      
    
    font = {'family' : 'serif', 'color'  : 'darkred',  'weight' : 'normal',  'size'   : 16 }
    lineType = ['g--', 'r-', 'k-.', 'b.']              # ['g', 'r-', 'k-', 'b-']
    leg = ['consensus Mouth Open model', 'personalized Mouth Open model','consensus Mouth Open model', 'personalized Mouth Open model']               # ['0', '0.1', '0.25', '0.4']
    
    ### plot PR curve
    fig = plt.figure()
    fig.patch.set_facecolor('white')
    
    plt.title('P-R curve', fontdict=font)
    plt.xlabel('recall', fontdict=font)
    plt.xticks(np.linspace(0, 1, 11))
    plt.yticks(np.linspace(0, 1, 11))
    plt.ylabel('precision', fontdict=font)
    plt.grid(True)    
    for i in range(len(groupTP)):
        plt.plot(groupTP[i], groupPrecision[i], lineType[i], linewidth=3, markersize = 10)
    
    plt.legend(leg, loc = 7)
    
    ### plot ROC curve
    fig = plt.figure()
    fig.patch.set_facecolor('white')
    
    plt.title('ROC curve', fontdict=font)
    plt.xlabel('FP rate', fontdict=font)
    plt.xticks(np.linspace(0, 1, 11))
    plt.yticks(np.linspace(0, 1, 11))
    plt.ylabel('TP rate (recall)', fontdict=font)
    plt.grid(True)    
    
    for i in range(len(groupTP)):
        plt.plot(groupFP[i], groupTP[i], lineType[i], linewidth=3, markersize = 10)
    
    plt.legend(leg, loc = 7)    
#========================================== Data Preparation ======================================

def retrieveData():
    global UoI
    mcl = pm.MongoClient('10.137.168.196:27017')        
    coll = mcl.DataSet['PMLExpression']
    originalData = {}
    for user in UoI.keys():
        originalData[user] = {'0':[], '1':[]}
    
    #for ent in coll.find({'userId': {'$in': UoI.keys()}}, {'_id':True, 'userId':True, 'labels':True}, timeout=False):
    for ent in coll.find({}, {'_id':True, 'userId':True, 'labels':True}, timeout=False):
        userId = ent['userId'] 

        if not userId in originalData:
            #if len(originalData.keys()) >= 8:    # control the number of total users
                #break
            originalData[userId] = {'0':[], '1':[]} 
            UoI[userId] = 0
            
#        if (stop_add_data(userId)):
#            continue
#        UoI[userId] += 1   
            
        if not len(ent['labels']) == 0:
            originalData[userId]['1'].append(ent['_id'])        # in the format of ObjectId
        else:
            originalData[userId]['0'].append(ent['_id'])             
        
    return originalData           
    

def splitData(originalData):
    global trainData
    global testData
    global fracTrain
    for user in originalData.keys():
        trainData[user] = []
        testData[user] = []
        numOfPosData = len(originalData[user]['1'])
        numOfNegData = len(originalData[user]['0'])
        pos = range(numOfPosData)
        neg = range(numOfNegData)
        selectedPos, selectedNeg = stratifiedSelection(pos, neg, fracTrain)        
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

def stratifiedSelection(posindex, negindex, fracTrain): 
    
    num = int(len(posindex)*fracTrain)
    selectPosIndex = sample(posindex, num)    
    num = int(len(negindex)*fracTrain)
    selectNegIndex = sample(negindex, num)    
    
    return selectPosIndex, selectNegIndex
    
def checkUserPartitionMapping():
    global users
    mcl = pm.MongoClient('10.137.168.196:27017')
    if not users: 
        userColl = mcl.DataSet['PMLUsers']
        for u in userColl.find(None, {'userId':True, 'partitionId':True}, timeout=False):
            users[u['userId']] = u['partitionId']
    mcl.close()

    
if __name__=='__main__':
    
    #prepareData()
    loadPreparedData("trainData", "testData")
    
#    print "add_users"
#    add_users()
#    print "add_data"
#    add_data()
#    print "train"
#    train(10)
    
    print "test"
    isPersonalized = False
    resGT = test(isPersonalized)
    destfile = open("resGT", 'w')       # save result and gt
    pickle.dump(resGT, destfile)
    destfile.close()
    
    print "evaluate"
#    file = open("resGT", 'r')
#    resGT = pickle.load(file)
#    file.close()
    evaluate(resGT, "acc.curve")
