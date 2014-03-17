# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 23:42:45 2014

@author: xm
"""
import yaml
import socket
from ..monk import get_UUID

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
        self.kafkaConnectionString = "mozo.cloudapp.net:9092"
        self.kafkaGroup = 'test'
        self.kafkaTopic = get_UUID()
        self.kafkaPartitionId = 0
        self.monkHost = socket.gethostbyname(socket.gethostname())
        self.monkPort = 8887
        
        self.dataDB = None
        self.modelDB = None
        
        with open(configurationFileName, 'r') as conf:
            self.__dict__.update(yaml.load(conf))
