# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:19 2013
The project object
@author: xm
"""
import os
from pymonk.core.uid import UID
from pymonk.core.crane import Crane
from pymonk.utils.utils import *
from bson.objectid import ObjectId
from pymongo.son_manipulator import SONManipulator

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
            self.creator = 'monk'
        if 'createdTime' not in self.__dict__:
            self.createdTime = datetime.now()
        if 'lastModified' not in self.__dict__:
            self.lastModified = datetime.now()
    
    def __defaults__(self):
        self._id = ObjectId()
        self.creator = 'monk'
        self.createdTime = datetime.now()
        self.lastModified = self.createdTime
        
    def generic(self):
        """ A shallow copy of the __dict__, 
        and make neccessary conversion as needed"""
        result = {}
        result.update(self.__dict__)
        result['_type'] = ['MONKObject']
        result['lastModified'] = datetime.now()
        return result
    
    @classmethod
    def create(cls, generic):
        return cls(generic)
        
class Transform(SONManipulator):
    def transform_incoming(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, MONKObject):
                son[key] = monkObjectFactory.encode(value)
            elif isinstance(value, dict): # Make sure we recurse into sub-docs
                son[key] = self.transform_incoming(value, collection)
        return son

    def transform_outgoing(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, dict):
                if "_type" in value and value["_type"][0] == "MONKObject":
                    son[key] = monkObjectFactory.decode(value)
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
        typeName = generic['_type'][-1]
        return self.factory[typeName](generic)

def loadOrCreateAll(store, objs):
    if objs and isinstance(objs[0], ObjectId):
        return store.loadAllByIds(objs)
    else:
        return map(monkObjectFactory.decode, objs)
        
monkObjectFactory = MONKObjectFactory()
monkTransformer = Transform()

class Configuration(object):
    def __init__(self, configurationFileName):
        self.modelConnectionString  = 'localhost'
        self.modelDataBaseName      = 'TestMONKModel'
        self.pandaCollectionName    = 'PandaStore'
        self.turtleCollectionName   = 'TurtleStore'
        self.mantisCollectionName   = 'MantisStore'
        self.monkeyCollectionName   = 'MonkeyStore'
        self.tigerCollectionName    = 'TigerStore'
        self.modelMaxCacheSize      = -1
        self.modelMaxCacheTime      = -1
        self.dataConnectionString   = 'localhost'
        self.dataDataBaseName       = 'TestMONKData'
        self.entityCollectionName   = 'EntityStore'
        self.relationCollectionName = 'RelationStore'
        self.dataMaxCacheSize = -1
        self.dataMaxCacheTime = -1
        self.logFileName = 'log'
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
mantisStore    = Crane(config.modelConnectionString,\
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
tigerStore    = Crane(config.modelConnectionString,\
                      config.modelDataBaseName,\
                      config.tigerCollectionName,\
                      monkTransformer,\
                      config.modelMaxCacheSize,\
                      config.modelMaxCacheTime)
