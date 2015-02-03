import sys
import numpy as np
import monk.core.api as monkapi
from monk.roles.configuration import get_config
from monk.roles.administrator import AdminBroker
from monk.roles.worker import WorkerBroker
from monk.roles.monitor import MonitorBroker
import pymongo as pm
import logging
logger = logging.getLogger('exper')

MonkConfigFile = 'monk_config.yml'
MouthOpenTurtleFile = 'mouthOpen-turtle.yml'
MouthOpenTurtle = 'mouthOpenTurtle'
MouthOpenEntityNumber = 151413

users = {}              # the list of users' names
trainData = {}          # the ObjectID of the selected data in DB
testData = {}           # the ObjectID of the selected data in DB
ab = {}
wb = {}
mb = {}

#def readline(f):
#    line = f.readline()
#    while line.strip() == '':
#        line = f.readline()
#    return line
#
#def readVector(f):
#    size = int(readline(f))
#    v = np.zeros(size)
#    for i in range(size):
#        v[i] = float(readline(f))
#    return v
#
#def readMatrix(f):
#    ns = readline(f).split()
#    nr = int(ns[0])
#    nc = int(ns[1])
#    m = np.zeros((nr,nc))
#    for i in range(nr*nc):
#        fs = readline(f).split()
#        r = int(fs[0])
#        c = int(fs[1])
#        v = float(fs[2])
#        m[r,c] = v
#    return m
#
#def readModel(filename):
#    userFactors = None
#    itemFactors = None
#    with open(filename) as f:
#        modelname = readline(f)
#        version = readline(f)
#        globalbias = float(readline(f))
#        minRate = int(readline(f))
#        maxRate = int(readline(f))
#        userBias = readVector(f)
#        userFactors = readMatrix(f)
#        itemBias = readVector(f)
#        itemFactors = readMatrix(f)
#    return userFactors, itemFactors
#
#def addUser(ab, num=6100, nameStub='mluser'):
#    ab.reconnect()
#    for i in range(num):
#        ab.add_user('{}{}'.format(nameStub, i))
#
#def cloneMovieLensTurtle(wb, master='monk', turtleName='movielens-binary', num=6100, nameStub='mluser'):
#    wb.reconnect()
#    for i in range(num):
#        wb.add_clone(master, turtleName, nameStub+str(i))
#
#def addRatingData(filename, itemFactors, turtleName, wb):
#    with open(filename) as f:
#        sts = readline(f).split()
#        userid = int(sts[0])
#        itemid = int(sts[1])
#        rating = int(sts[2])
#        # add data to user, turtleName
#        print userid, itemid, rating

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
    
    ab.add_user('monk')        
    users['monk'] = -1
    
#    ab.reconnect()
#    for ent in monkapi.load_entities_in_ids(num=MouthOpenEntityNumber):        #monkapi.load_entities(num=MouthOpenEntityNumber):
#        user = ent.userId    # error "*** TypeError: an integer is required" when using ent['userId']
#        ab.add_user(user)
        
def cloneTurtle():
    global wb
    global users
    wb.reconnect()
    for user in users:
        wb.add_clone('monk', MouthOpenTurtle, user)         

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
    for user in users:
        wb.save_turtle(user, MouthOpenTurtle)
        
def add_data():
    global users
    global trainData
    global wb
    for ent in monkapi.load_entities():
        entity = str(ent['_id'])
        user = ent['userId']
        if ent['_id'] in trainData[user]:
            wb.add_data(user, MouthOpenTurtle, entity)
    save_turtles()

def train(wb, nIter, master='monk', turtleName='movielens-binary', num=6100, nameStub='mluser'):
    wb.reconnect()
    for j in range(nIter):
        for i in range(num):
            user = nameStub+str(i)
            wb.train(user, turtleName)
            wb.merge(master, turtleName, user)
        logger.info('iteration {}'.format(i))
        
def reset_gamma(gamma):
    for user in users:
        wb.reset_parameter(user, MouthOpenTurtle, 'gamma', gamma)

def prepareTurtles():
    global users
   
    #add userto DB (Usually needs to do it at very first time)
    add_users()

    #load user from DB
#    users = load_users()
    
    #load turtle of monk from script and create a master turtle   
#    turtleScript = monkapi.yaml2json(MouthOpenTurtleFile)
#    monkapi.create_turtle(turtleScript)
#    #moTurtle = monkapi.load_turtle(MouthOpenTurtle, 'monk')
#    #moTurtle.save()        
    
    #clone turtle for all the users
    #cloneTurtle()
    
if __name__=='__main__':
    ab,wb,mb=initialize()    
    prepareTurtles()
    #prepareData()
    
    #add Data
    #add_data()

    #train
    #train()
    
#localhost:8888/accuracy?name=mouthOpenTurtle&accType=ROC