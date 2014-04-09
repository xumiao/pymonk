# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 23:42:45 2014

@author: xm
"""
import yaml
import socket
import constants

class Configuration(object):

    def __init__(self, configurationFileName=None):
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
                
        if configurationFileName:
            with open(configurationFileName, 'r') as conf:
                self.__dict__.update(yaml.load(conf))
        
        # TODO: factor it better
        if self.pandaFields is None:
            self.pandaFields = {}
        self.pandaFields[constants.WEIGHTS] = False
        if self.mantisFields is None:
            self.mantisFields = {}
        self.mantisFields[constants.DATA] = False
        if self.entityFields is None:
            self.entityFields = {}
        self.entityFields[constants.MONK_TYPE] = True
        self.entityFields[constants.FEATURES] = True
        self.entityFields[constants.RAWS] = True
        
