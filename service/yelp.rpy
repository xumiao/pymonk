# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 11:23:54 2013

@author: xumiao
"""

from defferedResource import DefferedResource
from twisted.web.resource import Resource
import pymongo as pm
import simplejson
from twisted.python import log
from recommender import scoring

collectionName = "Seattle"
num = 10

class Recommend(DefferedResource):
    def _delayedRender_POST(self, request):
        queryObj = eval(request.content.getvalue())
        hardConstraints = queryObj["hard"]
        softConstraints = queryObj["soft"]
        log.msg(hardConstraints)        
        log.msg(softConstraints)
        
        conn  = pm.Connection("localhost")
        db    = conn.local
        coll  = db[collectionName]
        geo   = hardConstraints["geo"]
        query = {"google_geometry.geometry.location":{"$within":{"$center":[[geo["x"], geo["y"]], geo["d"]]}}}
        log.msg(query)
        results = []        
        for ent in coll.find(query, {"_id":1, "comment":1, "title":1, "desc":1}).limit(num):
            score = scoring(ent, softConstraints)
            results.append({"id":str(ent["_id"]), "score":score})
        
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()

class Like(DefferedResource):
    def _delayedRender_POST(self, request):
        queryObj = eval(request.content.getvalue())
        originalQuery = queryObj["query"]
        likedId = queryObj["id"]
        hardConstraints = originalQuery["hard"]
        softConstraints = originalQuery["soft"]
        log.msg(hardConstraints)        
        log.msg(softConstraints)
        log.msg(likedId)
        
        conn  = pm.Connection("localhost")
        db    = conn.local
        coll  = db[collectionName]
        geo   = hardConstraints["geo"]
        query = {"google_geometry.geometry.location":{"$within":{"$center":[[geo["x"], geo["y"]], geo["d"]]}}}
        log.msg(query)

        results = [{"id":likedId, "score":10}]
        for ent in coll.find(query, {"_id":1, "comment":1, "title":1, "desc":1}).limit(num):
            if likedId == str(ent["_id"]):
                continue
            score = scoring(ent, softConstraints)
            results.append({"id":str(ent["_id"]), "score":score})
        if len(results) > num:
            results = results[0:-1]
        simplejson.dump(
        {
            "results" : results,
            "hasMore" : True
        }, request)
        request.finish()
    
class Skip(DefferedResource):
    def _delayedRender_POST(self, request):
        queryObj = eval(request.content.getvalue())
        originalQuery = queryObj["query"]
        skippedId = queryObj["id"]
        hardConstraints = originalQuery["hard"]
        softConstraints = originalQuery["soft"]
        log.msg(hardConstraints)        
        log.msg(softConstraints)
        log.msg(skippedId)
        
        conn  = pm.Connection("localhost")
        db    = conn.local
        coll  = db[collectionName]
        geo   = hardConstraints["geo"]
        query = {"google_geometry.geometry.location":{"$within":{"$center":[[geo["x"], geo["y"]], geo["d"]]}}}
        log.msg(query)

        results = []
        for ent in coll.find(query, {"_id":1, "comment":1, "title":1, "desc":1}).limit(num + 1):
            if skippedId == str(ent["_id"]):
                continue
            score = scoring(ent, softConstraints)
            results.append({"id":str(ent["_id"]), "score":score})
        if len(results) > num:
            results = results[0:-1]
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
