# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import logging
import logging.config
from bson.objectid import ObjectId
# to register classes in base
import base, crane, entity, relation, tigress, turtle, mantis, panda
import configuration
import yaml
from constants import *

logger = logging.getLogger("monk.api")
_config = None

# utility APIs
def UUID(objId=None):
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
    
def initialize(config=None):
    global _config
    if config is not None:
        if isinstance(config, basestring):
            _config = configuration.Configuration(config)
        else:
            _config = config
    
    logging.config.dictConfig(_config.loggingConfig)
    logger.info('------start up------')
    return crane.initialize_storage(_config)

def exits():
    if _config is None:
        return False
    logger.info('------end-----------')
    crane.exit_storage()
    return True

def reloads(config=None):
    if config is None:
        if _config is None:
            print 'configuration is not set'
            return
        else:
            config = _config
    
    exits()
    reload(base)
    reload(crane)
    reload(entity)
    reload(relation)
    reload(tigress)
    reload(turtle)
    reload(mantis)
    reload(panda)
    initialize(config)
    
# entity APIs
def load_entities(entities, query={}, skip=0, num=100, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    if not entities:
        entities = [ent['_id'] for ent in crane.entityStore.load_all_in_ids(query, skip, num)]
    return crane.entityStore.load_or_create_all(entities)

def load_entity(entity, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    return crane.entityStore.load_or_create(entity)

def save_entities(entities, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    [crane.entityStore.update_one_in_fields(ent, ent.generic()) for ent in entities]
    
# project(turtle) management APIs
def has_turtle(turtleName, user):
    return crane.turtleStore.has_user(turtleName, user)

def has_turtle_in_store(turtleName, user):
    return crane.turtleStore.has_user_in_store(turtleName, user)

def follow_turtle(turtleName, user, leader):
    if not has_turtle_in_store(turtleName, user):
        turtle = load_turtle(turtleName, leader)
        if not turtle:
            logger.error('turtle {0} with user {1} does not exists'.format(turtleName, leader))
            return None
        newTurtle = turtle.clone(user)
        turtle.followers.add(user)
        newTurtle.leader = leader
        newTurtle.save()
        crane.turtleStore.update_one_in_fields(turtle, {'followers':turtle.followers})
        return newTurtle
    else:
        logger.error('user {0} already has cloned this turtle'.format(user))
        return None

def unfollow_turtle(turtleName, user, leader):
    turtle = load_turtle(turtleName, leader)
    follower = load_turtle(turtleName, user)
    if not turtle or not follower:
        logger.error('turtle {0} has no user {1} or {2}'.format(turtleName, user, leader))
        return False
    turtle.followers.remove(user)
    crane.turtleStore.update_one_in_fields(turtle, {'followers':turtle.followers})
    follower.leader = None
    crane.turtleStore.update_one_in_fields(turtle, {'leader':None})

def find_turtles(query):
    ids = [t['_id'] for t in crane.turtleStore.load_all_in_ids(query, 0, 0)]
    return crane.turtleStore.load_all_by_ids(ids)
    
def create_turtle(turtleScript):
    _turtle = crane.turtleStore.load_or_create(turtleScript)
    if _turtle is None:
        logger.error('failed to load or create the turtle {0}'.format(turtleScript))
        return None
    return _turtle
    
def load_turtle(turtleName, user):
    return crane.turtleStore.load_one_by_name_user(turtleName, user)
        
def remove_turtle(turtleName, user, deep=False):
    turtle = load_turtle(turtleName, user)
    if not turtle:
        logger.error('turtle {0} has no user {1}'.format(turtleName, user))
        return False
        
    if turtle.leader:
        leadTurtle = load_turtle(turtleName, turtle.leader)
        leadTurtle.followers.remove(user)
        crane.turtleStore.update_one_in_fields(leadTurtle, {'followers':leadTurtle.followers})
    return turtle.delete(deep)
    
def entity_collection(turtleName, user):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        return _turtle.entityCollectionName
    else:
        logger.warning('can not find turtle {0}@{1} to get entity collection'.format(user, turtleName))
        return None

# pandas
def create_panda(pandaScript):
    return crane.pandaStore.load_or_create(pandaScript)

def find_pandas(query, fields=None):
    return crane.pandaStore.load_all(query, fields)

def add_panda(turtleName, user, panda):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        return _turtle.add_panda(panda)
    else:
        logger.warning('can not find turtle {0}@{1} to add panda {2}'.format(user, turtleName, panda.name))
        return None

def delete_panda(turtleName, user, panda):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        return _turtle.delete_panda(panda)
    else:
        logger.warning('can not find turtle {0}@{1} to add panda {2}'.format(user, turtleName, panda.name))
        return None
    
# training APIs
def add_data(turtleName, user, ent):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        crane.entityStore.set_collection_name(_turtle.entityCollectionName)
        ent = crane.entityStore.load_or_create(ent)
        return _turtle.add_data(ent)
    else:
        logger.warning('can not find turtle {0}@{1} to add data'.format(user, turtleName))
        return False

def train(turtleName, user):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        _turtle.train()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to train'.format(user, turtleName))
        return False

def commit(turtleName, user):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        _turtle.commit()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to commit'.format(user, turtleName))
        return False
    
def merge(turtleName, user, follower):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        return _turtle.merge(follower)
    else:
        logger.warning('can not find turtle by {0}@{1} to merge {2}'.format(user, turtleName, follower))
        return False
    
# testing APIs
def predict(turtleName, user, entity, fields=None):
    _turtle = crane.turtleStore.load_one_by_name_user(turtleName, user)
    if _turtle:
        return _turtle.predict(entity, fields)
    else:
        logger.warning('can not find turtle by {0}@{1} to predict'.format(user, turtleName))
        return 0
               
# meta query APIs
def find_type(typeName):
    return base.monkFactory.find(typeName)

def show_help():
    return {'help':'hello'}
