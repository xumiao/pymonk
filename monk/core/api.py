# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import logging
from constants import DEFAULT_CREATOR
from bson.objectid import ObjectId
# to register classes in base
import base, crane, entity, relation, tigress, turtle, mantis, panda, user, engine
import yaml

logger = logging.getLogger("monk.api")
_config = None
_initialized = False

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
    global _config, _initialized
    if _initialized:
        return
        
    if config is not None:
        _config = config

    logger.info('------start up------')
    _initialized = crane.initialize_storage(_config)
    return _initialized

def exits():
    global _initialized
    if _config is None:
        return False
    logger.info('------end-----------')
    crane.exit_storage()
    _initialized = False
    return True

def reloads(config=None):
    if config:
        exits()
        reload(crane)
        initialize(config)

    reload(user)
    reload(base)
    reload(panda)
    reload(tigress)
    reload(turtle)
    reload(mantis) 
    reload(entity)
    reload(relation)
    reload(engine)
    crane.reload_storage()

def dummy(duration):
    crane.entityStore.load_one_in_id({'name':'tests'})
    import time
    time.sleep(duration)
    
# entity APIs
def convert_entities(collectionName=None):
    crane.entityStore.set_collection_name(collectionName)
    return crane.entityStore.convert_to_MONKObject('Entity')
        
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
    
def load_entities_in_ids(query={}, skip=0, num=100):
    ids = [ent['_id'] for ent in crane.entityStore.load_all_in_ids(query, skip, num)]
    return ids

# engine APIs
def has_engine_in_store(engineName):
    logger.debug('engineStore {}@{}'.format(crane.engineStore._defaultCollectionName, crane.engineStore._database))
    return crane.engineStore.has_name_user(engineName, DEFAULT_CREATOR)

def find_engine(query):
    logger.debug('engineStore {}@{}'.format(crane.engineStore._defaultCollectionName, crane.engineStore._database))
    ids = [_engine['_id'] for _engine in crane.engineStore.load_all_in_ids(query, 0, 0)]
    return crane.engineStore.load_all_by_ids(ids)

def create_engine(engineScript):
    logger.debug('engineStore {}@{}'.format(crane.engineStore._defaultCollectionName, crane.engineStore._database))
    if 'monkType' not in engineScript:
        engineScript['monkType'] = 'Engine'
    _engine = crane.engineStore.load_or_create(engineScript, True)
    if _engine is None:
        logger.error('failed to load or create engine {}'.format(engineScript))
        return None
    return _engine

def load_engine(engineName):
    logger.debug('engineStore {}@{}'.format(crane.engineStore._defaultCollectionName, crane.engineStore._database))
    _engine = crane.engineStore.load_or_create({'name':engineName, 'creator':DEFAULT_CREATOR})
    if _engine is None:
        logger.error('engine {} does not exist'.format(engineName))
        return None
    return _engine

def save_engine(engineName):
    logger.debug('engineStore {}@{}'.format(crane.engineStore._defaultCollectionName, crane.engineStore._database))
    _engine = load_engine(engineName)
    if _engine:
        _engine.save()
        return True
    return False

def delete_engine(engineName):
    logger.debug('engineStore {}@{}'.format(crane.engineStore._defaultCollectionName, crane.engineStore._database))
    _engine = load_engine(engineName)
    if _engine:
        crane.engineStore.delete_by_id(_engine._id)
        return True
    return False
    
# user APIs
def has_user_in_store(userName):
    return crane.userStore.has_name_user(userName, DEFAULT_CREATOR)

def find_users(query):
    ids = [_user['_id'] for _user in crane.userStore.load_all_in_ids(query, 0, 0)]
    return crane.userStore.load_all_by_ids(ids)
    
def create_user(userScript):
    logger.debug('userScript {}'.format(userScript))
    if 'monkType' not in userScript:
        userScript['monkType'] = 'User'
    _user = crane.userStore.load_or_create(userScript, True)
    if _user is None:
        logger.error('failed to load or create user {0}'.format(userScript))
        return None
    if _user.password != userScript.get('password',''):
        logger.error('password is not correct for the user {0}'.format(_user.name))
        return None
    return _user
    
def load_user(userName, password=''):
    _user = crane.userStore.load_or_create({'name':userName, 'creator':DEFAULT_CREATOR})
    if _user is None:
        logger.error('user {0} does not exists'.format(userName))
        return None
    if _user.password != password:
        logger.error('wrong password {1} for user {0}'.format(userName, password))
        return None
    return _user

def save_user(userName, password=''):
    _user = load_user(userName, password)
    if _user:
        _user.save()
        return True
    return False
    
def delete_user(userName, password=''):
    _user = load_user(userName, password)
    if _user:
        crane.userStore.delete_by_id(_user._id)
        return True
    return False
        
# project(turtle) management APIs
def has_turtle_in_store(turtleName, userName):
    return crane.turtleStore.has_name_user(turtleName, userName)

def clone_turtle(turtleName, userName, follower):
    if not has_turtle_in_store(turtleName, follower):
        _turtle = load_turtle(turtleName, userName)
        if not _turtle:
            logger.error('turtle {0} with user {1} does not exists'.format(turtleName, userName))
            return None
        newTurtle = _turtle.clone(follower)
        newTurtle.leader = userName
        newTurtle.followers = []
        newTurtle.save()
        return newTurtle
    else:
        follow_turtle(turtleName, follower, leader=userName)
        logger.error('user {0} already has cloned this turtle'.format(userName))
        return None

def remove_turtle(turtleName, userName, deep=False):
    _turtle = load_turtle(turtleName, userName)
    if not _turtle:
        logger.error('turtle {0} has no user {1}'.format(turtleName, userName))
        return False
    return _turtle.delete(deep)

def follow_turtle(turtleName, userName, leader=None, follower=None):
    try:
        _turtle = load_turtle(turtleName, userName)
        rt = True
        if follower:
            rt = rt & _turtle.add_follower(follower)
        if leader:
            rt = rt & _turtle.add_leader(leader)
        return rt
    except Exception as e:
        logger.error(e)
        logger.error('can not find turtle {0}@{1}'.format(turtleName, userName))
        return False
                
def unfollow_turtle(turtleName, userName, leader=None, follower=None):
    try:
        _turtle = load_turtle(turtleName, userName)
        rt = True
        if follower:
            rt = rt & _turtle.remove_follower(follower)
        if leader:
            rt = rt & _turtle.remove_leader(leader)
        return rt
    except Exception as e:
        logger.error(e)
        logger.error('can not find turtle {0}@{1}'.format(turtleName, userName))
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
    
def load_turtle(turtleName, userName):
    return crane.turtleStore.load_or_create({'name':turtleName, 'creator':userName})

def save_turtle(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if not _turtle:
        logger.error('turtle {0} has no user {1}'.format(turtleName, userName))
        return False
    _turtle.save()
    return True
        
def entity_collection(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        return _turtle.entityCollectionName
    else:
        logger.warning('can not find turtle {0}@{1} to get entity collection'.format(userName, turtleName))
        return None

# pandas
def create_panda(pandaScript):
    return crane.pandaStore.load_or_create(pandaScript)

def find_pandas(query, fields=None):
    return crane.pandaStore.load_all(query, fields)

def add_panda(turtleName, userName, panda):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        return _turtle.add_panda(panda)
    else:
        logger.warning('can not find turtle {0}@{1} to add panda {2}'.format(userName, turtleName, panda.name))
        return None

def delete_panda(turtleName, userName, panda):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        return _turtle.delete_panda(panda)
    else:
        logger.warning('can not find turtle {0}@{1} to add panda {2}'.format(userName, turtleName, panda.name))
        return None
    
# training APIs
def add_data(turtleName, userName, ent):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        crane.entityStore.set_collection_name(_turtle.entityCollectionName)
        ent = crane.entityStore.load_or_create(UUID(ent), True)
        return _turtle.add_data(ent)
    else:
        logger.warning('can not find turtle {0}@{1} to add data'.format(userName, turtleName))
        return False

def checkout(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        _turtle.checkout()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to checkout'.format(userName, turtleName))
        return False
        
def train(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        _turtle.train()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to train'.format(userName, turtleName))
        return False
        
def get_leader(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        if _turtle.leader is None:
            return userName
        else:
            return _turtle.leader
    else:
        logger.warning('can not find turtle by {0}@{1} to get leader'.format(userName, turtleName))
        return None

def get_followers(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        return _turtle.followers
    else:
        return []
        
def commit(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        _turtle.commit()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to commit'.format(userName, turtleName))
        return False
        
def merge(turtleName, userName, follower):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        return _turtle.merge(follower)
    else:
        logger.warning('can not find turtle by {0}@{1} to merge {2}'.format(userName, turtleName, follower))
        return False

def set_mantis_parameter(turtleName, userName, para, value):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        _turtle.set_mantis_parameter(para, value)
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to set parameter'.format(userName, turtleName))
        return False
    
# testing APIs
def predict(turtleName, userName, entity, fields=None):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        entity = crane.entityStore.load_or_create(UUID(entity))
        return _turtle.predict(entity, fields)
    else:
        logger.warning('can not find turtle by {0}@{1} to predict'.format(userName, turtleName))
        return 0
        
def reset(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        _turtle.reset()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to reset'.format(userName, turtleName))
        return False
        
def reset_all_data(turtleName, userName):
    _turtle = load_turtle(turtleName, userName)
    if _turtle:
        _turtle.reset()
        _turtle.reset_data()
        return True
    else:
        logger.warning('can not find turtle by {0}@{1} to reset_all_data'.format(userName, turtleName))
        return False        
               
# meta query APIs
def find_type(typeName):
    return base.monkFactory.find(typeName)

def show_help():
    return {'help':'hello'}
