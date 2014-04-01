# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:56:41 2014
Execute turtle for each entity
@author: pacif_000
"""
import monk.core.api as monkapi
import zerorpc
import logging
import simplejson
from bson.objectid import ObjectId

monkapi.initialize("executor.yml")
logger = logging.getLogger("monk.executor")
default_turtle_id = ObjectId("5338c7562524830c64a2d599")

class Executor(object):

    def recommend_tags(self, turtle_id, user_context):
        turtle_id = default_turtle_id
        user_id = user_context['user_id']
        monkapi.find_turtle(turtle_id)
        if not monkapi.has_one(turtle_id, user_id):
            monkapi.load_one(turtle_id, user_id)
        ents = monkapi.get_entities()
        # @todo: add user_context features
        results = [(monkapi.predict(turtle_id, user_id, ent), ent.name) for ent in ents]
        results.sort(reverse=True)
        return simplejson.dumps([result[1] for result in results])

s = zerorpc.Server(Executor())
s.bind("tcp://0.0.0.0:4242")
s.run()
