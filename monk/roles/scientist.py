# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 09:07:52 2014
Data Scientist portal to feature engineering
@author: xm
"""
import monk.core.api as monkapi
import monk.core.configuration as Config
import logging
import os
import monk.utils.utils as utils

config = Config.Configuration("scientist.yml", "scientist", str(os.getpid()))
logger = logging.getLogger("monk.scientist")

userId = None

def login(user):
    global userId
    userId = user

def reloads():
    monkapi.exits()
    reload(monkapi)
    monkapi.reloads(config)

def starts():
    monkapi.initialize(config)
    
def exits():
    monkapi.exits()

def load_entities(query={}, skip=0, num=100, collectionName=None):
    return monkapi.load_entities(None, query, skip, num, collectionName)

def save_entities(ents, collectionName=None):
    monkapi.save_entities(ents, collectionName)
    
def show(ent, fields=None):
    utils.show(ent, fields)

def get_turtle(name):
    tuts = monkapi.find_turtles({'name':name})
    if tuts:
        return tuts[0]['_id']
    else:
        return None
        
def active_train(turtleId):
    if not userId:
        logger.info('please log in first')
        return
    turtle = monkapi.get_turtle(turtleId)
    turtle.active_train_one(userId)

def execute(turtleId, entities=None, fields=None, entityCollectionName=None):
    monkapi.crane.entityStore.set_collection_name(entityCollectionName)
    if entities is None:
        entities = monkapi.load_entities()
    [monkapi.predict(turtleId, userId, ent, fields) for ent in entities]
    monkapi.save_entities(entities, entityCollectionName)
    return entities

def add_panda(turtleId, pandaScript, run=True): 
    pass

def add_turtle(turtleScript):
    if userId and 'creator' not in turtleScript:
        turtleScript['creator'] = userId
    turtleId = monkapi.create_turtle(turtleScript)
    monkapi.save_turtle(turtleId)
    return turtleId
    
def train(turtleId, nIter=10):
    pass

