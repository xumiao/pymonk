import sys
import numpy as np

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

def addRatingData(filename, itemFactors, turtleName, wb):
    with open(filename) as f:
        sts = readline(f).split()
        userid = int(sts[0])
        itemid = int(sts[1])
        rating = int(sts[2])
        # add data to user, turtleName
        print userid, itemid, rating

if __name__=='__main__':
    readModel(sys.argv[1])
