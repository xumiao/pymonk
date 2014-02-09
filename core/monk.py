# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:19 2013
The project object
@author: xm
"""
import os
import socket
from pymonk.core.uid import UID
from pymonk.core.crane import Crane
from pymonk.utils.utils import *
from bson.objectid import ObjectId
from pymongo.son_manipulator import SONManipulator

__TYPE = '_type'
__DEFAULT_CREATOR = 'monk'
__DEFAULT_NONE = 'None'
__DEFAULT_EMPTY = ''

class MONKObject(object):
    def __init__(self, generic = None):
        if generic is not None:
            try:
                self.__dict__.update(generic)
                self.__restore__()
            except:
                self.__defaults__()
        else:
            self.__defaults__()
    
    def __restore__(self):
        if '_id' not in self.__dict__:
            self._id = ObjectId()
        if 'creator' not in self.__dict__:
            self.creator = __DEFAULT_CREATOR
        if 'createdTime' not in self.__dict__:
            self.createdTime = datetime.now()
        if 'lastModified' not in self.__dict__:
            self.lastModified = datetime.now()
    
    def __defaults__(self):
        self._id = ObjectId()
        self.creator = __DEFAULT_CREATOR
        self.createdTime = datetime.now()
        self.lastModified = self.createdTime
        
    def generic(self):
        """ A shallow copy of the __dict__, 
        and make neccessary conversion as needed"""
        result = {}
        result.update(self.__dict__)
        result[__TYPE] = ['MONKObject']
        result['lastModified'] = datetime.now()
        return result
        
    @classmethod
    def appendType(cls, result):
        result[__TYPE].append(cls.__name__)
        
    @classmethod
    def create(cls, generic):
        return cls(generic)
        
class Transform(SONManipulator):
    def transform_incoming(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, MONKObject):
                son[key] = monkFactory.encode(value)
            elif isinstance(value, dict): # Make sure we recurse into sub-docs
                son[key] = self.transform_incoming(value, collection)
        return son

    def transform_outgoing(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, dict):
                if __TYPE in value and value[__TYPE][0] == "MONKObject":
                    son[key] = monkFactory.decode(value)
                else: # Again, make sure to recurse into sub-docs
                    son[key] = self.transform_outgoing(value, collection)
        return son

class MONKObjectFactory(object):
    def __init__(self):
        self.factory = {}
        self.factory['MONKObject'] = MONKObject.create
    
    def register(self, typeName, createFunc):
        self.factory[typeName] = createFunc
    
    def encode(self, obj):
        return obj.generic()
        
    def decode(self, generic):
        typeName = generic[__TYPE][-1]
        return self.factory[typeName](generic)

    def load_or_create(self, store, obj):
        if obj and isinstance(obj, ObjectId):
            return store.loadOneById(obj)
        else:
            return self.decode(obj)
            
    def load_or_create_all(self, store, objs):
        if objs and isinstance(objs[0], ObjectId):
            return store.loadAllByIds(objs)
        else:
            return map(self.decode, objs)
        
monkFactory = MONKObjectFactory()
monkTransformer = Transform()

class Configuration(object):
    def __init__(self, configurationFileName):
        self.modelConnectionString  = 'localhost'
        self.modelDataBaseName      = 'TestMONKModel'
        self.pandaCollectionName    = 'PandaStore'
        self.turtleCollectionName   = 'TurtleStore'
        self.viperCollectionName    = 'ViperStore'
        self.mantisCollectionName   = 'MantisStore'
        self.monkeyCollectionName   = 'MonkeyStore'
        self.tigressCollectionName  = 'TigressStore'
        self.modelMaxCacheSize      = -1
        self.modelMaxCacheTime      = -1
        self.dataConnectionString   = 'localhost'
        self.dataDataBaseName       = 'TestMONKData'
        self.entityCollectionName   = 'EntityStore'
        self.relationCollectionName = 'RelationStore'
        self.dataMaxCacheSize = -1
        self.dataMaxCacheTime = -1
        self.logFileName = 'monk.log'
        self.monkHost = socket.gethostbyname(socket.gethostname())
        self.monkPort = 8887
        self.parse(configurationFileName)
        
    def parse(self, configurationFileName):
        configFile = file(configurationFileName, 'r')
        for line in configFile:
            line = line.strip()
            if not line.startswith('#') and line.find('=') > -1:
                kvp = line.split('=')
                self.__dict__[LowerFirst(kvp[0].strip())] = kvp[1].strip()
        configFile.close()

#@todo: change to scan paths
config = Configuration(os.getenv('MONK_CONFIG_FILE', 'monk.config'))

uidStore      = UID(config.modelConnectionString,\
                    config.modelDataBaseName)
entityStore   = Crane(config.dataConnectionString,\
                      config.dataDataBaseName,\
                      config.entityCollectionName,\
                      monkTransformer,\
                      config.dataMaxCacheSize,\
                      config.dataMaxCacheTime)
relationStore = Crane(config.dataConnectionString,\
                      config.dataDataBaseName,\
                      config.relationCollectionName,\
                      monkTransformer,\
                      config.dataMaxCacheSize,\
                      config.dataMaxCacheTime)
pandaStore    = Crane(config.modelConnectionString,\
                      config.modelDataBaseName,\
                      config.pandaCollectionName,\
                      monkTransformer,\
                      config.modelMaxCacheSize,\
                      config.modelMaxCacheTime)
mantisStore   = Crane(config.modelConnectionString,\
                      config.modelDataBaseName,\
                      config.mantisCollectionName,\
                      monkTransformer,\
                      config.modelMaxCacheSize,\
                      config.modelMaxCacheTime)
turtleStore   = Crane(config.modelConnectionString,\
                      config.modelDataBaseName,\
                      config.turtleCollectionName,\
                      monkTransformer,\
                      config.modelMaxCacheSize,\
                      config.modelMaxCacheTime)
monkeyStore   = Crane(config.modelConnectionString,\
                      config.modelDataBaseName,\
                      config.monkeyCollectionName,\
                      monkTransformer,\
                      config.modelMaxCacheSize,\
                      config.modelMaxCacheTime)
tigressStore  = Crane(config.modelConnectionString,\
                      config.modelDataBaseName,\
                      config.tigressCollectionName,\
                      monkTransformer,\
                      config.modelMaxCacheSize,\
                      config.modelMaxCacheTime)
viperStore    = Crane(config.modelConnectionString,\
                      config.modelDataBaseName,\
                      config.viperCollectionName,\
                      monkTransformer,\
                      config.modelMaxCacheSize,\
                      config.modelMaxCacheTime)                      
