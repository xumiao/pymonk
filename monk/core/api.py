# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import logging
from bson.objectid import ObjectId
# to register classes in base
import base, crane, entity, relation, tigress, turtle, mantis, panda

logger = logging.getLogger("monk")

def initialize(config):
    logging.basicConfig(format='[%(asctime)s]#[%(levelname)s] : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=eval(config.logLevel))
    
    crane.initialize_storage(config)
    
def get_UUID():
    return ObjectId()
    
# training APIs
def create_turtle(turtle_script):
    base.turtleStore.load_or_create(turtle_script)

def update_turtle(turtle_script):
    pass

def remove_turtle(turtle_script):
    pass

def add_data(turtle_id, partition_id, entity):
    _turtle = base.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        _turtle.add_data(partition_id, entity)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))

def train_one(turtle_id, partition_id):
    _turtle = base.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        _turtle.train_one(partition_id)
        _turtle.save_one(partition_id)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))

def aggregate(turtle_id, partition_id):
    _turtle = base.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        _turtle.aggregate(partition_id)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))
    
# testing APIs
def predict(turtle_id, partition_id, entity):
    _turtle = base.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        return _turtle.predict(partition_id, entity)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))

# storage APIs
def save_turtle(turtle_id, partition_id):
    _turtle = base.turtleStore.load_one_by_id(turtle_id)
    if _turtle:
        _turtle.save_one(partition_id)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))

# query APIs
def find_type(type_name):
    return base.monkFactory.find(type_name)


