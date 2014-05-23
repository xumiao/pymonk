# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 23:42:45 2014

@author: xm
"""
import yaml
import socket

class Configuration(object):

    def __init__(self, configurationFileName=None, logFileMidName='', pid=''):
        self.uidConnectionString = 'localhost'
        self.uidDataBaseName = 'uidDB'
        self.modelConnectionString = 'localhost'
        self.modelDataBaseName = 'TestMONKModel'
        self.pandaCollectionName = 'PandaStore'
        self.pandaFields = None
        self.turtleCollectionName = 'TurtleStore'
        self.turtleFields = None
        self.mantisCollectionName = 'MantisStore'
        self.mantisFields = None
        self.tigressCollectionName = 'TigressStore'
        self.tigressFields = None
        
        self.dataConnectionString = 'localhost'
        self.dataDataBaseName = 'TestMONKData'
        self.entityCollectionName = 'EntityStore'
        self.entityFields = None
        
        self.kafkaConnectionString = "mozo.cloudapp.net:9092"
        self.kafkaGroup = 'test'
        self.kafkaTopic = 'test_topic'
        self.kafkaMasterPartition = 0
        self.kafkaPartitions = [1]
        self.monkHost = socket.gethostbyname(socket.gethostname())
        self.monkPort = 8887
        
        self.logFileNameStub = 'logs/monk'
        if configurationFileName:
            with open(configurationFileName, 'r') as conf:
                self.__dict__.update(yaml.load(conf))
        
        if logFileMidName:
            self.loggingConfig['handlers']['files']['filename'] = \
            '.'.join([self.logFileNameStub, logFileMidName, pid, 'log'])
                