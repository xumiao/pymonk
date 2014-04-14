# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import logging
from bson.objectid import ObjectId
# to register classes in base
import base, crane, entity, relation, tigress, turtle, mantis, panda
import configuration
import os
import yaml
from constants import *

logger = logging.getLogger("monk.api")

# utility APIs
def get_UUID(objId=None):
    if objId is None:
        return ObjectId()
    elif isinstance(objId, basestring):
        return ObjectId(objId)
    else:
        return objId

def yaml2json(yamlFileName):
    with open(yamlFileName, 'r') as yf:
        return yaml.load(yf)
    return None
    
def initialize(config):
    if isinstance(config, basestring):
        config = configuration.Configuration(config)
    
    pid = os.getpid()
    logging.basicConfig(filename='{0}.{1}.log'.format(config.logFileName, pid),
                        filemode='w',
                        format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=eval(config.logLevel))
#    logging.basicConfig(format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
#                        datefmt='%m/%d/%Y %I:%M:%S %p',
#                        level=eval(config.logLevel))
    
    return crane.initialize_storage(config)

def exits():
    crane.exit_storage()
    return True

# entity APIs
def get_entities(query=None, fields=None):
    return crane.entityStore.load_all(query, fields)

def load_entities(entities):
    return crane.entityStore.load_or_create_all(entities)

def load_entity(entity):
    return crane.entityStore.load_or_create(entity)
    
# project(turtle) management APIs
def find_turtle(turtleScript):
    _turtle = crane.turtleStore.load_or_create(turtleScript)
    if _turtle is None:
        logger.error('failed to load or create the turtle {0}'.format(turtleScript))
        return None
    return _turtle._id

def save_turtle(turtleId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        crane.turtleStore.save_one(_turtle)
        return True
    else:
        logger.error('failed to save turtle {0}'.format(turtleId))
        return False

def remove_turtle(turtleId):
    pass

# training APIs
def add_data(turtleId, partitionId, ent):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        crane.entityStore.set_collection_name(_turtle.entityCollectionName)
        ent = crane.entityStore.load_or_create(ent)
        return _turtle.add_data(partitionId, ent)
    else:
        logger.warning('can not find turtle by {0} to add data'.format(turtleId))

def train_one(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        _turtle.train_one(partitionId)
        _turtle.save_one(partitionId)
    else:
        logger.warning('can not find turtle by {0} to train'.format(turtleId))

def aggregate(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        _turtle.aggregate(partitionId)
    else:
        logger.warning('can not find turtle by {0} to aggregate'.format(turtleId))
    
# testing APIs
def predict(turtleId, partitionId, entity):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.predict(partitionId, entity)
    else:
        logger.warning('can not find turtle by {0} to predict'.format(turtleId))

# partition APIs
def has_one_in_store(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.has_partition_in_store(partitionId)
    else:
        logger.warning('can not find turtle by {0} to save a partition'.format(turtleId))
        return False

def has_one(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.has_partition(partitionId)
    else:
        logger.warning('can not find turtle by {0} to save a partition'.format(turtleId))
        return False

def save_one(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.save_one(partitionId)
    else:
        logger.warning('can not find turtle by {0} to save a partition'.format(turtleId))
        return False

def add_one(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.add_one(partitionId)
    else:
        logger.warning('can not find turtle by {0} to add a partition'.format(turtleId))
        return False

def remove_one(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.remove_one(partitionId)
    else:
        logger.warning('can not find turtle by {0} to remove a partition'.format(turtleId))
        return False

def load_one(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.load_one(partitionId)
    else:
        logger.warning('can not find turtle by {0} to load a partition'.format(turtleId))
        return False

def unload_one(turtleId, partitionId):
    _turtle = crane.turtleStore.load_one_by_id(turtleId)
    if _turtle:
        return _turtle.unload_one(partitionId)
    else:
        logger.warning('can not find turtle by {0} to unload a partition'.format(turtleId))
        return False
                
# meta query APIs
def find_type(typeName):
    return base.monkFactory.find(typeName)

