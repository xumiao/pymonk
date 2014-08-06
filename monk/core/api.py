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


def dummy(duration):
    crane.entityStore.load_one_in_id({'name':'tests'})
    import time
    time.sleep(duration)
    

# entity APIs
def load_entities(entities=[], query={}, skip=0, num=100, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    if not entities:
        entities = [ent['_id'] for ent in crane.entityStore.load_all_in_ids(query, skip, num)]
    return crane.entityStore.load_or_create_all(entities)

def save_entities(entities, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    [crane.entityStore.update_one_in_fields(ent, ent.generic()) for ent in entities]

def load_entity(entity, collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    return crane.entityStore.load_or_create(entity)
    
# project(turtle) management APIs
def has_turtle_in_store(turtleName, user):
    return crane.turtleStore.has_name_user(turtleName, user)

def clone_turtle(turtleName, user, follower):
    if not has_turtle_in_store(turtleName, follower):
        _turtle = load_turtle(turtleName, user)
        if not _turtle:
            logger.error('turtle {0} with user {1} does not exists'.format(turtleName, user))
            return None
        newTurtle = _turtle.clone(follower)
        newTurtle.leader = user
        newTurtle.followers = []
        newTurtle.save()
        return newTurtle
    else:
        follow_turtle_follower(turtleName, follower, user)
        logger.error('user {0} already has cloned this turtle'.format(user))
        return None

def remove_turtle(turtleName, user, deep=False):
    _turtle = load_turtle(turtleName, user)
    if not _turtle:
        logger.error('turtle {0} has no user {1}'.format(turtleName, user))
        return False
    return _turtle.delete(deep)

def follow_turtle_leader(turtleName, user, follower):
    try:
        _turtle = load_turtle(turtleName, user)
        _turtle.add_follower(follower)
        return True
    except Exception as e:
        logger.error(e)
        logger.error('can not find turtle {0}@{1}'.format(turtleName, user))
        return False
        
def follow_turtle_follower(turtleName, user, leader):
    try:
        _turtle = load_turtle(turtleName, user)
        _turtle.add_leader(leader)
        return True
    except Exception as e:
        logger.error(e)
        logger.error('can not find turtle {0}@{1}'.format(turtleName, user))
        return False
        
def unfollow_turtle_leader(turtleName, user, follower):
    try:
        _turtle = load_turtle(turtleName, user)
        _turtle.remove_follower(follower)
        return True
    except Exception as e:
        logger.error(e)
        logger.error('can not find turtle {0}@{1}'.format(turtleName, user))
        return False
        
def unfollow_turtle_follower(turtleName, user, leader):
    try:
        _turtle = load_turtle(turtleName, user)
        _turtle.remove_leader()
        return True
    except Exception as e:
        logger.error(e)
        logger.error('can not find turtle {0}@{1}'.format(turtleName, user))
        return False

def find_turtles(query):
    ids = [t['_id'] for t in crane.turtleStore.load_all_in_ids(query, 0, 0)]
    return crane.turtleStore.load_all_by_ids(ids)
    
def create_turtle(turtleScript):
    _turtle = crane.turtleStore.load_or_create(turtleScript, True)
    if _turtle is None:
        logger.error('failed to load or create the turtle {0}'.format(turtleScript))
        return None
    return _turtle
    
def load_turtle(turtleName, user):
    return crane.turtleStore.load_or_create({'name':turtleName, 'creator':user})

def save_turtle(turtleName, user):
    _turtle = load_turtle(turtleName, user)
    if not _turtle:
        logger.error('turtle {0} has no user {1}'.format(turtleName, user))
        return False
    _turtle.save()
    return True
        
def entity_collection(turtleName, user):
    _turtle = load_turtle(turtleName, user)
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
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        return _turtle.add_panda(panda)
    else:
        logger.warning('can not find turtle {0}@{1} to add panda {2}'.format(user, turtleName, panda.name))
        return None

def delete_panda(turtleName, user, panda):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        return _turtle.delete_panda(panda)
    else:
        logger.warning('can not find turtle {0}@{1} to add panda {2}'.format(user, turtleName, panda.name))
        return None
    
# training APIs
def add_data(turtleName, user, ent):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        crane.entityStore.set_collection_name(_turtle.entityCollectionName)
        ent = crane.entityStore.load_or_create(ObjectId(ent))
        return _turtle.add_data(ent)
    else:
        logger.warning('can not find turtle {0}@{1} to add data'.format(user, turtleName))
        return False

def checkout(turtleName, user):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        _turtle.checkout()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to checkout'.format(user, turtleName))
        return False
        
def train(turtleName, user):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        _turtle.train()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to train'.format(user, turtleName))
        return False
        
def get_leader(turtleName, user):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        if _turtle.leader is None:
            return user
        else:
            return _turtle.leader
    else:
        logger.warning('can not find turtle by {0}@{1} to get leader'.format(user, turtleName))
        return None
        
def commit(turtleName, user):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        _turtle.commit()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to commit'.format(user, turtleName))
        return False
        
def merge(turtleName, user, follower):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        return _turtle.merge(follower)
    else:
        logger.warning('can not find turtle by {0}@{1} to merge {2}'.format(user, turtleName, follower))
        return False

def set_mantis_parameter(turtleName, user, para, value):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        _turtle.set_mantis_parameter(para, value)
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to set parameter'.format(user, turtleName))
        return False
    
# testing APIs
def predict(turtleName, user, entity, fields=None):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        #crane.entityStore.set_collection_name(_turtle.entityCollectionName)
        entity = crane.entityStore.load_or_create(ObjectId(entity))
        return _turtle.predict(entity, fields)
    else:
        logger.warning('can not find turtle by {0}@{1} to predict'.format(user, turtleName))
        return 0
        
def test_data(turtleName, user, entity):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        #crane.entityStore.set_collection_name(_turtle.entityCollectionName)
        entity = crane.entityStore.load_or_create(ObjectId(entity))
        return _turtle.test_data(entity)
    else:
        logger.warning('can not find turtle by {0}@{1} to test data'.format(user, turtleName))
        return 0        

def reset(turtleName, user):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        _turtle.reset()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to reset'.format(user, turtleName))
        return False
        
def reset_all_data(turtleName, user):
    _turtle = load_turtle(turtleName, user)
    if _turtle:
        _turtle.reset()
        _turtle.reset_data()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to reset_all_data'.format(user, turtleName))
        return False        
               
# meta query APIs
def find_type(typeName):
    return base.monkFactory.find(typeName)

def show_help():
    return {'help':'hello'}
