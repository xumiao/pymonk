# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import logging
from uid import UID
from bson.objectid import ObjectId
from crane import Crane
import base
logger = logging.getLogger("monk")

def initialize(config):
    logging.basicConfig(format='[%(asctime)s]#[%(levelname)s] : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=eval(config.logLevel))
    
    dataDB = Crane.getDatabase(config.dataConnectionString,
                               config.dataDataBaseName)
    modelDB = Crane.getDatabase(config.modelConnectionString,
                                config.modelDataBaseName)
    uidDB = Crane.getDatabase(config.uidConnectionString,
                              config.uidDataBaseName)
                              
    base.dataDB = dataDB
    base.modelDB = modelDB
    base.uidDB = uidDB
    
    logger.info('initializing uid store')
    base.uidStore = UID(uidDB)
    
    logger.info('initializing entity store')
    base.entityStore = Crane(dataDB,
                        config.entityCollectionName,
                        config.entityFields)
                        
    logger.info('initializing relation store')
    base.relationStore = Crane(dataDB,
                          config.relationCollectionName,
                          config.relationFields)
    
    logger.info('initializing panda store')
    base.pandaStore = Crane(modelDB,
                       config.pandaCollectionName,
                       config.pandaFields)
    
    logger.info('initializing mantis store')
    base.mantisStore = Crane(modelDB,
                        config.mantisCollectionName,
                        config.mantisFields)
    
    logger.info('initializing turtle store')
    base.turtleStore = Crane(modelDB,
                        config.turtleCollectionName,
                        config.turtleFields)
    
    logger.info('initializing tigress store')
    base.tigressStore = Crane(modelDB,
                         config.tigressCollectionName,
                         config.tigressFields)
    
    logger.info('initializing viper store')
    base.viperStore = Crane(modelDB,
                       config.viperCollectionName,
                       config.viperFields)
    
def get_UUID():
    return ObjectId()
    
# training APIs
def create_turtle(turtle):
    base.turtleStore.load_or_create(turtle)

def update_turtle(turtle):
    pass

def remove_turtle(turtle):
    pass

def add_data(turtle_id, partition_id, entity, fields):
    turtle = base.turtleStore.load_one_by_id(turtle_id)
    if turtle:
        turtle.add_data(partition_id, entity, fields)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))

def train_one(turtle_id, partition_id):
    turtle = base.turtleStore.load_one_by_id(turtle_id)
    if turtle:
        turtle.train_one(partition_id)
        turtle.save_one(partition_id)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))

def aggregate(turtle_id, partition_id):
    turtle = base.turtleStore.load_one_by_id(turtle_id)
    if turtle:
        turtle.aggregate(partition_id)
    else:
        logger.warning('can not find turtle by {0}'.format(turtle_id))
    
# testing APIs
def predict(turtle_id, partition_id, entity, fields):
    pass

# query APIs
def find_type(type_name):
    return base.monkFactory.find(type_name)

# storage APIs
def save_turtle(turtle_id, partition_id):
    pass


