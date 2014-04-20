# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 16:20:55 2014

@author: pacif_000
"""
from defferedResource import DefferedResource
from twisted.web.resource import Resource
import simplejson
import logging
import monk.core.api as monkapi
from monk.core.configuration import Configuration
import os
from bson.objectid import ObjectId

config = Configuration("executor.yml")
pid = os.getpid()
fn = config.loggingConfig['handlers']['files']['filename']
config.loggingConfig['handlers']['files']['filename'] = '.'.join([fn[:-4],'executor_rest',str(pid),'log'])

monkapi.initialize(config)
logger = logging.getLogger("monk.executor")

class Recommend(DefferedResource):
    
    def _recommend(self, args):
        turtleId = args.get('turtleId')
        userContext = args.get('userContext')
        entityIds = args.get('entityIds')
        if not turtleId or not userContext:
            logger.error('turtleId {0} userContext {1}'.format(turtleId, userContext))
            results = []
        else:
            turtleId = ObjectId(turtleId)
            userId = userContext['userId']
            if not monkapi.has_one(turtleId, userId):
                if not monkapi.has_one_in_store(turtleId, userId):
                    monkapi.add_one(turtleId, userId)
                else:
                    monkapi.load_one(turtleId, userId)
            entityCollectionName = monkapi.entity_collection(turtleId)
            ents = monkapi.load_entities(entityIds, entityCollectionName)
            # @todo: add user_context features
            results = [(monkapi.predict(turtleId, userId, ent), ent) for ent in ents]
            results.sort(reverse=True)
        return results
        
    def _delayedRender_GET(self, request):
        query = request.content.getvalue()
        args = simplejson.loads(query)
        results = self._recommend(args)
        simplejson.dump(
        {
            "results":[result[1] for result in results]
        }, request)
        request.finish()
        
    def _delayedRender_POST(self, request):
        query = request.content.getvalue()
        args = simplejson.loads(query)
        results = self._recommend(args)
        simplejson.dump(
        {
            "results":[result[1] for result in results]
        }, request)
        request.finish()
        
resource = Resource()
resource.putChild("recommend", Recommend())