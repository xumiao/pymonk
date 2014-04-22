# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 16:20:55 2014

@author: pacif_000
"""
import os
import simplejson
import logging
from bson.objectid import ObjectId
from twisted.web import server
from twisted.internet import reactor

from deffered_resource import DefferedResource
import monk.core.api as monkapi
import monk.core.constants as cons
import monk.core.configuration as Config

from monk.utils.utils import DateTimeEncoder

config = Config.Configuration("executor.yml", "executorREST", str(os.getpid()))
monkapi.initialize(config)
logger = logging.getLogger("monk.executor")

class MonkAPI(server.Site):
    def stopFactory(self):
        monkapi.exits()
        server.Site.stopFactory(self)
        
class Recommend(DefferedResource):
    isLeaf = True
    def __init__(self, turtleId=None, delayTime=0.0):
        DefferedResource.__init__(self, delayTime)
        self.defaultTurtleId = turtleId
        self.defaultUserContext = {'userId' : cons.DEFAULT_USER}
    
    def _filter(self, ent, fields):
        if fields:
            return {field:getattr(ent, field, '') for field in fields}
        else:
            return ent.generic()
        
    def _recommend(self, args):
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
            ents = monkapi.load_entities(None, query, num * 10, entityCollectionName)
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
        logger.info('request {0}'.format(request.args))
        results = self._recommend(request.args)
        simplejson.dump(results, request, cls=DateTimeEncoder)
        request.finish()
        
    def _delayedRender_POST(self, request):
        logger.info('request {0}'.format(request.args))
        results = self._recommend(request.args)
        simplejson.dump(results, request, cls=DateTimeEncoder)
        request.finish()

root = DefferedResource()
root.putChild("recommend", Recommend())
root.putChild("recommendTags", Recommend("5338c7562524830c64a2d599"))

site = MonkAPI(root, "web.log")
reactor.listenTCP(8080, site)
reactor.run()
