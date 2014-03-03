# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:19 2013
The project object
@author: xm
"""
import socket
import logging
from monk.utils.utils import *
from bson.objectid import ObjectId
from pymongo.son_manipulator import SONManipulator

__TYPE = '_type'
__DEFAULT_CREATOR = 'monk'
__DEFAULT_NONE = 'None'
__DEFAULT_EMPTY = ''


class MONKObject(object):

    def __init__(self, generic=None):
        if generic is not None:
            try:
                self.__dict__.update(generic)
                self.__restore__()
            except Exception as e:
                logging.warning('serializatin failed. {0}'.format(e.message))
                logging.info('defaulting')
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
            elif isinstance(value, dict):  # Make sure we recurse into sub-docs
                son[key] = self.transform_incoming(value, collection)
        return son

    def transform_outgoing(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, dict):
                if __TYPE in value and value[__TYPE][0] == "MONKObject":
                    son[key] = monkFactory.decode(value)
                else:  # Again, make sure to recurse into sub-docs
                    son[key] = self.transform_outgoing(value, collection)
        return son


class MONKObjectFactory(object):

    def __init__(self):
        self.factory = {}
        self.factory['MONKObject'] = MONKObject.create

    def register(self, MONKObjectClass):
        self.factory[MONKObjectClass.__name__] = MONKObjectClass.create

    def encode(self, obj):
        return obj.generic()

    def decode(self, generic):
        typeName = generic[__TYPE][-1]
        return self.factory[typeName](generic)

    def load_or_create(self, store, obj):
        if obj and isinstance(obj, ObjectId):
            return store.load_one_by_id(obj)
        else:
            return self.decode(obj)

    def load_or_create_all(self, store, objs):
        if objs and isinstance(objs[0], ObjectId):
            return store.load_one_by_ids(objs)
        else:
            return map(self.decode, objs)
    
    def clone(self, obj, modification = {}):
        try:
            generic = obj.generic()
            generic['_id'] = ObjectId()
            generic['creator'] = __DEFAULT_CREATOR
            generic['createdTime'] = datetime.now()
            generic['lastModified'] = datetime.now()            
            generic.update(modification)
            return self.decode(generic)
        except Exception as e:
            logging.warning('can not clone the object {0}'.format(e.message))
            return None


monkFactory = MONKObjectFactory()
monkTransformer = Transform()

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
        self.parse(configurationFileName)

    def parse(self, configurationFileName):
        configFile = file(configurationFileName, 'r')
        for line in configFile:
            line = line.strip()
            if not line.startswith('#') and line.find('=') > -1:
                kvp = line.split('=')
                self.__dict__[LowerFirst(kvp[0].strip())] = kvp[1].strip()
        configFile.close()

