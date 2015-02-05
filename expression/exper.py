import sys
import numpy as np
import monk.core.api as monkapi
from monk.roles.configuration import get_config
from monk.roles.administrator import AdminBroker
from monk.roles.worker import WorkerBroker
from monk.roles.monitor import MonitorBroker
import pymongo as pm
import logging
import pickle
from random import sample
logger = logging.getLogger('exper')

MonkConfigFile = 'monk_config.yml'
MouthOpenTurtleFile = 'mouthOpen-turtle.yml'
MouthOpenTurtle = 'mouthOpenTurtle'
MouthOpenEntityNumber = 151413
MasterName = 'monk'
FracTrain = 0.5

users = {}              # the list of users' names
trainData = {}          # the ObjectID of the selected data in DB
testData = {}           # the ObjectID of the selected data in DB
UoI = {}
ab = {}
wb = {}
mb = {}

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

#========================================== Data Preparation ======================================

def retrieveData():
    global UoI
    mcl = pm.MongoClient('localhost')        
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
        selectedPos, selectedNeg = stratifiedSelection(pos, neg, FracTrain)        
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
#    if len(posindex) > 0:
#        num = 1
#    else:
#        num = 0
    selectPosIndex = sample(posindex, num)    
    num = int(len(negindex)*fracTrain)
#    if len(negindex) > 0:
#        num = 1
#    else:
#        num = 0
    selectNegIndex = sample(negindex, num)    
    
    return selectPosIndex, selectNegIndex


def initialize():
    global ab
    global wb
    global mb
    config = get_config(MonkConfigFile, 'exper', '')
    ab = AdminBroker(config.kafkaConnectionString, config.administratorGroup, config.administratorTopic, producerType=AdminBroker.FIXED_PRODUCER, producerPartitions=[0])
    wb = WorkerBroker(config.kafkaConnectionString, config.workerGroup, config.workerTopic, producerType=WorkerBroker.USER_PRODUCER)
    mb = MonitorBroker(config.kafkaConnectionString, config.monitorGroup, config.monitorTopic, producerType=MonitorBroker.FIXED_PRODUCER, producerPartitions=[0])
    monkapi.exits()
    monkapi.initialize(config)
    return ab, wb, mb
    
def add_users():
    global users
    mcl = pm.MongoClient('localhost')    
    coll = mcl.DataSet['PMLExpression']
    
    ab.reconnect()
    
    for ent in coll.find(None, {'_id':True, 'userId':True}, timeout=False):
        follower = ent['userId']
        if follower not in users:
            users[follower] = -1
            ab.add_user(follower)
    
    ab.add_user(MasterName)        
    users[MasterName] = -1
    
#    ab.reconnect()
#    for ent in monkapi.load_entities_in_ids(num=MouthOpenEntityNumber):        #monkapi.load_entities(num=MouthOpenEntityNumber):
#        user = ent.userId    # error "*** TypeError: an integer is required" when using ent['userId']
#        ab.add_user(user)
        
def cloneTurtle():
    global wb
    global users
    wb.reconnect()
    for user in users:
        if user is not MasterName:
            wb.add_clone(MasterName, MouthOpenTurtle, user)         

def load_users():
    global users
    userIds = [user['_id'] for user in monkapi.crane.userStore.load_all_in_ids(None)]
    for userId in userIds:
        user = monkapi.crane.userStore.load_or_create(userId)
        userName = user.name
        if userName not in users:
            users[userName] = -1
    return users
    
def save_turtles():
    global users
    for user in users:
        wb.save_turtle(user, MouthOpenTurtle)
        
def add_data():
    global users
    global trainData
    global wb
    mcl = pm.MongoClient('localhost')        
    coll = mcl.DataSet['PMLExpression']
    
    #for ent in monkapi.load_entities():
    for ent in coll.find(None, {'_id':True, 'userId':True}, timeout=False):
        entity = str(ent['_id'])
        user = ent['userId']
        if ent['_id'] in trainData[user]:
            wb.add_data(user, MouthOpenTurtle, entity)
    save_turtles()

def train(nIter, master, turtleName):
    global wb
    global users
    wb.reconnect()
    for j in range(nIter):
        for user in users:
            wb.train(user, turtleName)
            wb.merge(master, turtleName, user)
        logger.info('iteration {}'.format(j))
        
def reset_gamma(gamma):
    for user in users:
        wb.reset_parameter(user, MouthOpenTurtle, 'gamma', gamma)

def prepareTurtles():
    global users
   
    #add userto DB (Usually needs to do it at very first time)
#    add_users()
    
    #load turtle of monk from script and create a master turtle   
#    turtleScript = monkapi.yaml2json(MouthOpenTurtleFile)
#    monkapi.create_turtle(turtleScript)
#    #moTurtle = monkapi.load_turtle(MouthOpenTurtle, 'monk')
#    #moTurtle.save()        
    
    #clone turtle for all the users
    cloneTurtle()
    
if __name__=='__main__':
    ab,wb,mb=initialize()    
    #prepareTurtles()
    #prepareData()
    
    #load user from DB
    users = load_users()
    
    #load data
    #loadPreparedData("trainData", "testData")
    
    #add data
    #add_data()

    #train
    train(10, MasterName, MouthOpenTurtle)
    
#localhost:8888/accuracy?name=mouthOpenTurtle&accType=ROC