# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 18:44:07 2014

@author: xumiao
"""

import pymongo as pm

def cleanupUser():
    mcl = pm.MongoClient('10.137.168.196:27017')
    coll = mcl['DataSet']['PMLExpression']
    ents = coll.find(None,{'_id':1, 'userId':1})
    for ent in ents:
        userId = ent['userId'].replace('.','').replace(' ','')
        if not userId == ent['userId']:
            coll.update({'_id':ent['_id']}, {'$set':{'userId':userId}})
    mcl.close()

if __name__=='__main__':
    cleanupUser()