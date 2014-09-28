# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 23:42:45 2014

@author: xm
"""
import yaml
import socket

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
        self.workerCollectionName  = 'WorkerStore'
        
        self.kafkaConnectionString = 'localhost'
        self.kafkaGroup = 'test'
        self.kafkaTopic = 'test_topic'
        self.monkHost = socket.gethostbyname(socket.gethostname())
        self.monkPort = 8887
        
        self.logFileNameStub = 'logs/monk'
        if configurationFileName:
            with open(configurationFileName, 'r') as conf:
                self.__dict__.update(yaml.load(conf))
        
        if logFileMidName:
            self.loggingConfig['handlers']['files']['filename'] = \
            '.'.join([self.logFileNameStub, logFileMidName, pid, 'log'])
                