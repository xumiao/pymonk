# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 17:34:34 2013

@author: xm
"""


from defferedResource import DefferedResource
from twisted.web.resource import Resource
import pymongo as pm
import simplejson
from twisted.python import log

dbName = "Products"
collectionName = "Jeans"
num = 20

def stringfy(x):
    x["_id"] = str(x["_id"])
    return x
    
class Recommend(DefferedResource):
    def _delayedRender_GET(self, request):
        conn  = pm.Connection("localhost")
        db    = conn[dbName]
        coll  = db[collectionName]
        results = map(stringfy, coll.find().limit(num))
        
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()
        
    def _delayedRender_POST(self, request):
        queryObj = eval(request.content.getvalue())
        hardConstraints = queryObj["hard"]
        softConstraints = queryObj["soft"]
        log.msg(hardConstraints)    
        log.msg(softConstraints)
        
        conn  = pm.Connection("localhost")
        db    = conn[dbName]
        coll  = db[collectionName]
        results = map(stringfy, coll.find().limit(num))
        
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()

class Like(DefferedResource):
    def _delayedRender_GET(self, request):
        conn  = pm.Connection("localhost")
        db    = conn[dbName]
        coll  = db[collectionName]
        results = map(stringfy, coll.find().limit(num))
        
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()

    def _delayedRender_POST(self, request):
        queryObj = eval(request.content.getvalue())
        originalQuery = queryObj["query"]
        likedId = queryObj["id"]
        hardConstraints = originalQuery["hard"]
        softConstraints = originalQuery["soft"]

        log.msg(hardConstraints)    
        log.msg(softConstraints)
        
        conn  = pm.Connection("localhost")
        db    = conn[dbName]
        coll  = db[collectionName]
        results = map(stringfy, coll.find().limit(num))
        
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()
    
class Skip(DefferedResource):
    def _delayedRender_GET(self, request):
        conn  = pm.Connection("localhost")
        db    = conn[dbName]
        coll  = db[collectionName]
        results = map(stringfy, coll.find().limit(num))
        
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()
        
    def _delayedRender_POST(self, request):
        queryObj = eval(request.content.getvalue())
        originalQuery = queryObj["query"]
        skippedId = queryObj["id"]
        hardConstraints = originalQuery["hard"]
        softConstraints = originalQuery["soft"]
        log.msg(hardConstraints)    
        log.msg(softConstraints)
        
        conn  = pm.Connection("localhost")
        db    = conn[dbName]
        coll  = db[collectionName]
        results = map(stringfy, coll.find().limit(num))
        
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()
    
resource = Resource()
resource.putChild("recommend", Recommend())
resource.putChild("like", Like())
resource.putChild("skip", Skip())