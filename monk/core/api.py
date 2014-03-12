# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import socket
import os
import logging
from uid import UID
from crane import Crane
import base
import yaml

class Configuration(object):

    def __init__(self, configurationFileName):
        self.uidConnectionString = 'localhost'
        self.uidDataBaseName = 'uidDB'
        self.modelConnectionString = 'localhost'
        self.modelDataBaseName = 'TestMONKModel'
        self.pandaCollectionName = 'PandaStore'
        self.pandaFields = {}
        self.turtleCollectionName = 'TurtleStore'
        self.turtleFields = {}
        self.viperCollectionName = 'ViperStore'
        self.viperFields = {}
        self.mantisCollectionName = 'MantisStore'
        self.mantisFields = {}
        self.monkeyCollectionName = 'MonkeyStore'
        self.monkeyFields = {}
        self.tigressCollectionName = 'TigressStore'
        self.tigressFields = {}
        self.dataConnectionString = 'localhost'
        self.dataDataBaseName = 'TestMONKData'
        self.entityCollectionName = 'EntityStore'
        self.entityFields = {} 
        self.relationCollectionName = 'RelationStore'
        self.relationFields = {}
        self.logFileName = 'monk.log'
        self.logLevel = 'logging.DEBUG'
        self.monkHost = socket.gethostbyname(socket.gethostname())
        self.monkPort = 8887
        
        self.dataDB = None
        self.modelDB = None
        
        with open(configurationFileName, 'r') as conf:
            self.__dict__.update(yaml.load(conf))

def initialize(monkConfigFile = None):
    if not monkConfigFile:
        #@todo: change to scan paths
        monkConfigFile = os.getenv('MONK_CONFIG_FILE', 'monk.yml')
    
    config = Configuration(monkConfigFile)
    
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
    
    logging.info('initializing uid store')
    base.uidStore = UID(uidDB)
    logging.info('finished uid store')
    
    logging.info('initializing entity store')
    base.entityStore = Crane(dataDB,
                        config.entityCollectionName,
                        config.entityFields)
    logging.info('finished entity store')
    logging.info('initializing relation store')
    base.relationStore = Crane(dataDB,
                          config.relationCollectionName,
                          config.relationFields)
    logging.info('finished relation store')
    logging.info('initializing panda store')
    base.pandaStore = Crane(modelDB,
                       config.pandaCollectionName,
                       config.pandaFields)
    logging.info('finished panda store')
    logging.info('initializing mantis store')
    base.mantisStore = Crane(modelDB,
                        config.mantisCollectionName,
                        config.mantisFields)
    logging.info('finished mantis store')
    logging.info('initializing turtle store')
    base.turtleStore = Crane(modelDB,
                        config.turtleCollectionName,
                        config.turtleFields)
    logging.info('finished turtle store')
    logging.info('initializing monkey store')
    base.monkeyStore = Crane(modelDB,
                        config.monkeyCollectionName,
                        config.monkeyFields)
    logging.info('finished monkey store')
    logging.info('initializing tigress store')
    base.tigressStore = Crane(modelDB,
                         config.tigressCollectionName,
                         config.tigressFields)
    logging.info('finished tigress store')
    logging.info('initializing viper store')
    base.viperStore = Crane(modelDB,
                       config.viperCollectionName,
                       config.viperFields)
    logging.info('finished viper store')

# training APIs
def create_turtle(turtle):
    base.turtleStore.load_or_create(turtle)

def update_turtle(turtle):
    pass

def remove_turtle(turtle):
    pass

def add_data(turtle_id, partition_id, entity, fields):
    pass

def mod_data(turtle_id, partition_id, entity, fields):
    pass

def train_one(turtle_id, partition_id):
    turtle = base.turtleStore.load_one_by_id(turtle_id)
    if turtle:
        turtle.train_one(partition_id)
    else:
        logging.warning('can not find turtle by {0}'.format(turtle_id))

# testing APIs
def process(turtle_id, partition_id, entity, fields):
    pass

# query APIs
def find_type(type_name):
    return base.monkFactory.find(type_name)

# storage APIs
def save():
    pass


