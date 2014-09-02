# -*- coding: utf-8 -*-
"""
Created on Mon Mar 31 13:20:46 2014

@author: xumiao
"""
from pymongo import MongoClient
from bson.objectid import ObjectId
from itertools import izip
from multiprocessing import Process

def migrateEnt(srcDataCollection, dstDataCollection, labelName, ents):
    conn = MongoClient(host="10.137.168.196", port=27017)
    db = conn.DataSet
    srcFrameColl = db[srcDataCollection+'Frames']
    dstColl = db[dstDataCollection]
    for userId, videoId, split, frames in ents:
        dstEnts = dstColl.find({'userId':userId, 'videoId':videoId},{'labels':1, 'frameNum':1})
        dstEnts = {e['frameNum']: e for e in dstEnts}
        frames = [ObjectId(frame) for frame in frames]
        frames = srcFrameColl.find({'_id':{'$in':frames}})
        numDoc = 0
        for frame in frames:
            frameNum = frame['Frame']
            label = frame['Label']
            if frameNum in dstEnts:
                if label > 0:
                    labels = dstEnts['labels']
                    labels.append(labelName)
                    dstColl.update({'userId':userId, 'videoId':videoId, 'frameNum':frameNum}, 
                                   {'$set':{'labels': labels}})
            else:
                features = frame['Features']
                features = [(k+1, v) for k, v in izip(range(len(features)), features)]
                labels = []
                if label > 0:
                    labels.append(labelName)
                dstEnt = {'userId':userId, 
                          'videoId':videoId, 
                          'split':split,
                          '_features':features, 
                          'labels':labels, 
                          'frameNum':frameNum}
                dstColl.insert(dstEnt)
            numDoc += 1
        print videoId, numDoc, ' processed'
    conn.close()
    print 'finished ', len(ents)

class Processing(object):
    
    def __init__(self, srcData, dstData, labelName, numProcess):
        self.srcData = srcData
        self.dstData = dstData
        self.labelName = labelName
        self.numProcess = numProcess
        self.data = [[] for n in range(numProcess)]
        self.currInd = 0
        
    def addData(self, ent):
        self.data[self.currInd].append(ent)
        self.currInd += 1
        if self.currInd >= self.numProcess:
            self.currInd = 0
    
    def start(self):
        self.ps = []
        for i in xrange(self.numProcess):
            p = Process(target=migrateEnt, args=(self.srcData, self.dstData, self.labelName, self.data[i]))
            self.ps.append(p)
            p.start()
    
    def join(self):
        [p.join() for p in self.ps]
            
if __name__=='__main__':
    procs = Processing("PMLMouthOpenTV", "PMLExpression", "mouthOpen", 10)
    conn = MongoClient(host="10.137.168.196", port=27017)
    db = conn.DataSet
    srcColl = db["PMLMouthOpenTV"]
    [procs.addData((ent['Name'], ent['_id'], ent['VideoDataSet'], ent['Frames'])) for ent in srcColl.find() if 'Frames' in ent and len(ent['Frames']) > 1]
    print 'start processing'
    procs.start()
    print 'waiting for join'
    procs.join()
    conn.close()
