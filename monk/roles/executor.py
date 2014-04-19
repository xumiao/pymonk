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

def get_entities(self, args):
    args = simplejson.loads(args)
    query = args.get('query')
    fields = args.get('fields')
    return monkapi.get_entities(query, fields)

def load_entities(self, args):
    args = simplejson.loads(args)
    entities = args.get('entities')
    return monkapi.load_entities(entities)

def load_entity(self, args):
    args = simplejson.loads(args)
    entity = args.get('entity')
    return monkapi.load_entity(entity)
    
def find_turtle(self, args):
    args = simplejson.loads(args)
    turtleScript = args.get('turtleScript')
    return monkapi.find_turtle(turtleScript)

def save_turtle(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    return monkapi.save_turtle(ObjectId(turtleId))

def remove_turtle(self, args):
    pass

def add_data(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    ent = args.get('ent')
    return monkapi.add_data(ObjectId(turtleId), userId, ent)

def train_one(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.train_one(ObjectId(turtleId), userId)

def aggregate(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.aggregate(ObjectId(turtleId), userId)
    
def predict(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    entity = args.get('entity')
    if not turtleId or userId:
        return False
    return monkapi.predict(ObjectId(turtleId), userId, entity)
    
def has_one_in_store(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.has_one_in_store(ObjectId(turtleId), userId)

def has_one(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.has_one(ObjectId(turtleId), userId)

def save_one(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.save_one(ObjectId(turtleId), userId)

def add_one(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.add_one(ObjectId(turtleId), userId)

def remove_one(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.remove_one(ObjectId(turtleId), userId)

def load_one(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.load_one(ObjectId(turtleId), userId)

def unload_one(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userId = args.get('userId')
    if not turtleId or userId:
        return False
    return monkapi.unload_one(ObjectId(turtleId), userId)
                
def find_type(self, args):
    args = simplejson.loads(args)
    typeName = args.get('typeName')
    return monkapi.find_type(typeName)

def recommend(self, args):
    args = simplejson.loads(args)
    turtleId = args.get('turtleId')
    userContext = args.get('userContext')
    entityIds = args.get('entityIds')
    if not turtleId or not userContext:
        logger.warning('turtleId {0} userContext {1}'.format(turtleId, userContext))
        return []
    turtleId = ObjectId(turtleId)
    userId = userContext['userId']
    if not monkapi.has_one(turtleId, userId):
        if not monkapi.has_one_in_store(turtleId, userId):
            monkapi.add_one(turtleId, userId)
        else:
            monkapi.load_one(turtleId, userId)
    ents = monkapi.load_entities(entityIds)
    # @todo: add user_context features
    results = [(monkapi.predict(turtleId, userId, ent), ent._id) for ent in ents]
    results.sort(reverse=True)
    return simplejson.dumps([{'id':str(result[1]), 'score':result[0]} for result in results])

s = zerorpc.Server(Executor())
s.bind("tcp://0.0.0.0:4242")
try:
    s.run()
finally:
    monkapi.exits()
    s.close()
