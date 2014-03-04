# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
import socket
import os
import logging
from monk.utils.utils import LowerFirst
from monk.core.uid import UID
from monk.core.crane import Crane
import monk.core.base as base

class Configuration(object):

    def __init__(self, configurationFileName):
        self.modelConnectionString = 'localhost'
        self.modelDataBaseName = 'TestMONKModel'
        self.pandaCollectionName = 'PandaStore'
        self.pandaFields = '{}'
        self.turtleCollectionName = 'TurtleStore'
        self.turtleFields = '{}'
        self.viperCollectionName = 'ViperStore'
        self.viperFields = '{}'
        self.mantisCollectionName = 'MantisStore'
        self.mantisFields = '{}'
        self.monkeyCollectionName = 'MonkeyStore'
        self.monkeyFields = '{}'
        self.tigressCollectionName = 'TigressStore'
        self.tigressFields = '{}'
        self.dataConnectionString = 'localhost'
        self.dataDataBaseName = 'TestMONKData'
        self.entityCollectionName = 'EntityStore'
        self.entityFields = '{}'
        self.relationCollectionName = 'RelationStore'
        self.relationFields = '{}'
        self.logFileName = 'monk.log'
        self.logLevel = 'logging.DEBUG'
        self.monkHost = socket.gethostbyname(socket.gethostname())
        self.monkPort = 8887
        
        self.dataDB = None
        self.modelDB = None
        
        self.parse(configurationFileName)

    def parse(self, configurationFileName):
        with open(configurationFileName, 'r') as configFile:
            for line in configFile:
                line = line.strip()
                if not line.startswith('#') and line.find('=') > -1:
                    kvp = line.split('=')
                    self.__dict__[LowerFirst(kvp[0].strip())] = kvp[1].strip()

def initialize(monkConfigFile = None):
    if not monkConfigFile:
        #@todo: change to scan paths
        #@todo: change to yml file for configuration
        monkConfigFile = os.getenv('MONK_CONFIG_FILE', 'monk.config')
    
    config = Configuration(monkConfigFile)
    
    logging.basicConfig(format='[%(asctime)s]#[%(levelname)s] : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=eval(config.logLevel))
    
    dataDB = Crane.getDatabase(config.dataConnectionString,
                               config.dataDataBaseName)
    modelDB = Crane.getDatabase(config.modelConnectionString,
                                config.modelDataBaseName)
    config.dataDB = dataDB
    config.modelDB = modelDB
    
    logging.info('initializing uid store')
    base.uidStore = UID(modelDB)
    logging.info('finished uid store')
    
    logging.info('initializing entity store')
    base.entityStore = Crane(dataDB,
                        config.entityCollectionName,
                        eval(config.entityFields))
    logging.info('finished entity store')
    logging.info('initializing relation store')
    base.relationStore = Crane(dataDB,
                          config.relationCollectionName,
                          eval(config.relationFields))
    logging.info('finished relation store')
    logging.info('initializing panda store')
    base.pandaStore = Crane(modelDB,
                       config.pandaCollectionName,
                       eval(config.pandaFields))
    logging.info('finished panda store')
    logging.info('initializing mantis store')
    base.mantisStore = Crane(modelDB,
                        config.mantisCollectionName,
                        eval(config.mantisFields))
    logging.info('finished mantis store')
    logging.info('initializing turtle store')
    base.turtleStore = Crane(modelDB,
                        config.turtleCollectionName,
                        eval(config.turtleFields))
    logging.info('finished turtle store')
    logging.info('initializing monkey store')
    base.monkeyStore = Crane(modelDB,
                        config.monkeyCollectionName,
                        eval(config.monkeyFields))
    logging.info('finished monkey store')
    logging.info('initializing tigress store')
    base.tigressStore = Crane(modelDB,
                         config.tigressCollectionName,
                         eval(config.tigressFields))
    logging.info('finished tigress store')
    logging.info('initializing viper store')
    base.viperStore = Crane(modelDB,
                       config.viperCollectionName,
                       eval(config.viperFields))
    logging.info('finished viper store')
    
