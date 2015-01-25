import sys
import numpy as np
import monk.core.api as monkapi
from monk.roles.configuration import get_config
from monk.roles.administrator import AdminBroker
from monk.roles.worker import WorkerBroker
from monk.roles.monitor import MonitorBroker
import logging
logger = logging.getLogger('exper')

def readline(f):
    line = f.readline()
    while line.strip() == '':
        line = f.readline()
    return line

def readVector(f):
    size = int(readline(f))
    v = np.zeros(size)
    for i in range(size):
        v[i] = float(readline(f))
    return v

def readMatrix(f):
    ns = readline(f).split()
    nr = int(ns[0])
    nc = int(ns[1])
    m = np.zeros((nr,nc))
    for i in range(nr*nc):
        fs = readline(f).split()
        r = int(fs[0])
        c = int(fs[1])
        v = float(fs[2])
        m[r,c] = v
    return m

def readModel(filename):
    userFactors = None
    itemFactors = None
    with open(filename) as f:
        modelname = readline(f)
        version = readline(f)
        globalbias = float(readline(f))
        minRate = int(readline(f))
        maxRate = int(readline(f))
        userBias = readVector(f)
        userFactors = readMatrix(f)
        itemBias = readVector(f)
        itemFactors = readMatrix(f)
    return userFactors, itemFactors

def addUser(ab, num=6100, nameStub='mluser'):
    ab.reconnect()
    for i in range(num):
        ab.add_user('{}{}'.format(nameStub, i))

def cloneMovieLensTurtle(wb, master='monk', turtleName='movielens-binary', num=6100, nameStub='mluser'):
    wb.reconnect()
    for i in range(num):
        wb.add_clone(master, turtleName, nameStub+str(i))

def addRatingData(filename, itemFactors, turtleName, wb):
    with open(filename) as f:
        sts = readline(f).split()
        userid = int(sts[0])
        itemid = int(sts[1])
        rating = int(sts[2])
        # add data to user, turtleName
        print userid, itemid, rating

def initialize():
    config = get_config('monk_config.yml', 'exper', '')
    ab = AdminBroker(config.kafkaConnectionString, config.administratorGroup, config.administratorTopic, producerType=AdminBroker.FIXED_PRODUCER, producerPartitions=[0])
    wb = WorkerBroker(config.kafkaConnectionString, config.workerGroup, config.workerTopic, producerType=WorkerBroker.USER_PRODUCER)
    mb = MonitorBroker(config.kafkaConnectionString, config.monitorGroup, config.monitorTopic, producerType=MonitorBroker.FIXED_PRODUCER, producerPartitions=[0])
    monkapi.exits()
    monkapi.initialize(config)
    return ab, wb, mb

def train(wb, nIter, master='monk', turtleName='movielens-binary', num=6100, nameStub='mluser'):
    wb.reconnect()
    for j in range(nIter):
        for i in range(num):
            user = nameStub+str(i)
            wb.train(user, turtleName)
            wb.merge(master, turtleName, user)
        logger.info('iteration {}'.format(i))
        
if __name__=='__main__':
    ab,wb,mb=initialize()
    userFactors, itemFactors = readModel(sys.argv[1])
    cloneMovieLensTurtle(wb)
    #addRatingData(sys.argv[2], itemFactors, 'movielens-binary', wb)
    #train(1)
    
