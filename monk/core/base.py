# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:19 2013
The project object
@author: xm
"""
import logging
from datetime import datetime
from bson.objectid import ObjectId
logger = logging.getLogger("monk")

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
                logger.warning('serializatin failed. {0}'.format(e.message))
                logger.info('defaulting')
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


class MONKObjectFactory(object):

    def __init__(self):
        self.factory = {}
        self.factory['MONKObject'] = MONKObject.create

    def register(self, MONKObjectClass):
        self.factory[MONKObjectClass.__name__] = MONKObjectClass.create

    def find(self, name):
        return [key for key in self.factory.iterkeys if key.find(name) >= 0]
        
    def encode(self, obj):
        return obj.generic()

    def decode(self, generic):
        typeName = generic[__TYPE][-1]
        return self.factory[typeName](generic)

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
            logger.warning('can not clone the object {0}'.format(e.message))
            return None


monkFactory = MONKObjectFactory()

uidStore = None
entityStore = None
relationStore = None
pandaStore = None
mantisStore = None
turtleStore = None
monkeyStore = None
tigressStore = None
viperStore = None
