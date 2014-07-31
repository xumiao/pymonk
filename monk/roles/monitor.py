# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 09:09:06 2014
Build a report page to monitor different MONK services
@author: xm
"""
import os
import simplejson
import logging
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from bson.objectid import ObjectId
from twisted.web import server
from twisted.internet import reactor
from deffered_resource import DefferedResource

metrics = {}
time_interval = 10000 #10 seconds
time_span = 1000000 #1000 seconds

class MonkMetrics(object):
    def __init__(self, hosts):
        self.kafka_client = KafkaClient(hosts)
        self.consumer = SimpleConsumer(self.kafka_client, )

class MonkMonitor(server.Site):
    def stopFactory(self):
        server.Site.stopFactory(self)

class Users(DefferedResource):
    isLeaf = True
    def __init__(self, delayTime=0.0):
        DefferedResource.__init__(self, delayTime)
    
    def _get_users(self, args):
        try:
            if 'turtleId' in args:
                turtleId = ObjectId(args['turtleId'][0])
            else:
                turtleId = ObjectId(self.defaultTurtleId)
            if 'userContext' in args:
                userContext = simplejson.loads(args.get('userContext')[0])
            else:
                userContext = self.defaultUserContext
            userId = userContext['userId']
            if 'query' in args:
                query = simplejson.loads(args.get('query')[0])
            else:
                query = {}
            if 'skip' in args:
                skip = int(args.get('skip')[0])
            else:
                skip = 0
            if 'num' in args:
                num = int(args.get('num')[0])
            else:
                num = 10
            if 'fields' in args:
                fields = simplejson.loads(args['fields'][0])
            else:
                fields = None
            if not monkapi.has_one(turtleId, userId):
                if not monkapi.has_one_in_store(turtleId, userId):
                    monkapi.add_one(turtleId, userId)
                else:
                    monkapi.load_one(turtleId, userId)
            entityCollectionName = monkapi.entity_collection(turtleId)
            ents = monkapi.load_entities(None, query, skip, num * 10, entityCollectionName)
            # @todo: add user_context features
            results = [(monkapi.predict(turtleId, userId, ent), ent) for ent in ents]
            results.sort(reverse=True)
        except Exception as e:
            logger.error(e.message)
            logger.error(e.args)
            logger.error('can not parse request {0}'.format(args))
            results = []
        return [self._filter(res[1], fields) for res in results]
        
    def _delayedRender_GET(self, request):
        results = self._get_users(request.args)
        simplejson.dump(results, request)
        request.finish()
        
    def _delayedRender_POST(self, request):
        results = self._get_users(request.args)
        simplejson.dump(results, request)
        request.finish()

   
root = DefferedResource()
root.putChild("users", Users())
root.putChild("metrics", Metrics())

site = MonkMonitor(root, "web.log")
reactor.listenTCP(8080, site)
reactor.run()
