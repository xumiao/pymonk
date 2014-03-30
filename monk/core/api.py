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

logger = logging.getLogger("monk.api")

# utility APIs
def get_UUID():
    return ObjectId()

def yaml2json(yamlFileName):
    with open(yamlFileName, 'r') as yf:
        return yaml.load(yf)
    return None
    
def initialize(config):
    if isinstance(config, basestring):
        config = configuration.Configuration(config)
    
#    pid = os.getpid()
#    logging.basicConfig(filename='{0}.{1}.log'.format(config.logFileName, pid),
#                        filemode='w',
#                        format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
#                        datefmt='%m/%d/%Y %I:%M:%S %p',
#                        level=eval(config.logLevel))
    logging.basicConfig(format='[%(asctime)s][%(name)-12s][%(levelname)-8s] : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=eval(config.logLevel))
    
    return crane.initialize_storage(config)

def exit():
    return True

# project(turtle) management APIs
def find_turtle(turtle_script):
    t = crane.turtleStore.load_or_create(turtle_script)
    if turtle is None:
        logger.error('failed to load or create the turtle {0}'.format(turtle_script))
        return None
    return t._id

def update_turtle(turtle_id):
    pass

def remove_turtle(turtle_id):
    pass

# training APIs
def add_data(turtle_id, partition_id, entity):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.add_data(partition_id, entity)
    else:
        logger.warning('can not find turtle by {0} to add data'.format(turtle_id))

def train_one(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        _turtle.train_one(partition_id)
        _turtle.save_one(partition_id)
    else:
        logger.warning('can not find turtle by {0} to train'.format(turtle_id))

def aggregate(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        _turtle.aggregate(partition_id)
    else:
        logger.warning('can not find turtle by {0} to aggregate'.format(turtle_id))
    
# testing APIs
def predict(turtle_id, partition_id, entity):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.predict(partition_id, entity)
    else:
        logger.warning('can not find turtle by {0} to predict'.format(turtle_id))

# partition APIs
def has_one_in_store(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.has_partition_in_store(partition_id)
    else:
        logger.warning('can not find turtle by {0} to save a partition'.format(turtle_id))
        return False

def has_one(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.has_partition(partition_id)
    else:
        logger.warning('can not find turtle by {0} to save a partition'.format(turtle_id))
        return False

def save_one(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.save_one(partition_id)
    else:
        logger.warning('can not find turtle by {0} to save a partition'.format(turtle_id))
        return False

def add_one(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.add_one(partition_id)
    else:
        logger.warning('can not find turtle by {0} to add a partition'.format(turtle_id))
        return False

def remove_one(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.remove_one(partition_id)
    else:
        logger.warning('can not find turtle by {0} to remove a partition'.format(turtle_id))
        return False

def load_one(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.load_one(partition_id)
    else:
        logger.warning('can not find turtle by {0} to load a partition'.format(turtle_id))
        return False

def unload_one(turtle_id, partition_id):
    _turtle = crane.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.unload_one(partition_id)
    else:
        logger.warning('can not find turtle by {0} to unload a partition'.format(turtle_id))
        return False
                
# meta query APIs
def find_type(type_name):
    return base.monkFactory.find(type_name)

