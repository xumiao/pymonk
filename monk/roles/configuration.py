# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 23:42:45 2014

@author: xm
"""
import yaml
import logging

class Configuration(object):

    def __init__(self, configurationFileName=None, logFileMidName='', pid=''):
        self.uidConnectionString   = 'localhost'
        self.uidDataBaseName       = 'UIDDB'
        
        self.modelConnectionString = 'localhost'
        self.modelDataBaseName     = 'MONKModelTest'
        self.userCollectionName    = 'UserStore'
        self.pandaCollectionName   = 'PandaStore'
        self.turtleCollectionName  = 'TurtleStore'
        self.mantisCollectionName  = 'MantisStore'
        self.tigressCollectionName = 'TigressStore'
        
        self.dataConnectionString  = 'localhost'
        self.dataDataBaseName      = 'MONKDataTest'
        self.entityCollectionName  = 'EntityStore'
        
        self.sysConnectionString   = 'localhost'
        self.sysDataBaseName       = 'MONKSysTest'
        self.engineCollectionName  = 'EngineStore'
        
        self.kafkaConnectionString = 'localhost'
        
        self.workerGroup = 'monkTest'
        self.workerTopic = 'monkTest'
        self.workerMaintenanceInterval = 60 #1 heartbeat per minute
        
        self.administratorGroup = 'monkTestAdmin'
        self.administratorTopic = 'monkTestAdmin'
        self.administratorServerPartitions = [0]
        self.administratorClientPartitions = [1]
        
        self.brokerTimeout = 200
        
        self.logFileNameStub = 'logs/monk'
        
        if configurationFileName:
            with open(configurationFileName, 'r') as conf:
                self.__dict__.update(yaml.load(conf))
        
        if 'loggingConfig' not in self.__dict__:
            with open('log_config.yml', 'r') as logConf:
                loggingConfig = yaml.load(logConf)
        elif isinstance(self.loggingConfig, str):
            with open(self.loggingConfig, 'r') as logConf:
                loggingConfig = yaml.load(logConf)
        else:
            loggingConfig = self.loggingConfig
            
        if logFileMidName:
            loggingConfig['handlers']['files']['filename'] = \
            '.'.join([self.logFileNameStub, logFileMidName, pid, 'log'])
        
        logging.config.dictConfig(loggingConfig)
