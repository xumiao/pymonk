# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 16:20:55 2014

@author: pacif_000
"""
import zerorpc
from defferedResource import DefferedResource
from twisted.web.resource import Resource
import simplejson
import logging

class Recommend(DefferedResource):
    def __init__(self):
        self.turtleId = "5338c7562524830c64a2d599"
        self.userId = "tester"
        self.client = zerorpc.Client()
        self.client.bind("tcp://*:4242", heartbeat=None)
        
    def _delayedRender_GET(self, request):
        query = request.content.getvalue()
        args = simplejson.dumps({
            "turtleId":self.turtleId,
            "userContext":{
                "userId":self.userId
            },
            "planContext":{
            }
        })
        results = self.client.recommend(args)
        simplejson.dump(
        {
            "results":results
        }, request)
        request.finish()
        
    def _delayedRender_POST(self, request):
        query = request.content.getvalue()
        args = simplejson.dumps({
            "turtleId":self.turtleId,
            "userContext":{
                "userId":self.userId
            },
            "planContext":{
            }
        })
        results = self.client.recommend(args)
        simplejson.dump(
        {
            "results":results
        }, request)
        request.finish()

resource = Resource()
resource.putChild("recommend", Recommend())