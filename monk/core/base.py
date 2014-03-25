# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:19 2013
The project object
@author: xm
"""
import logging
import constants
from datetime import datetime
from bson.objectid import ObjectId
logger = logging.getLogger("monk.base")

class MONKObject(object):

    def __init__(self, generic=None):
        if generic:
            try:
                logger.debug('trying to deserialize {0}'.format(generic))
                self.__dict__.update(generic)
            except Exception as e:
                logger.warning('deserializatin failed. {0}'.format(e.message))
                logger.warning('defaulting')
        self.__restore__()

    def __restore__(self):
        if '_id' not in self.__dict__:
            self._id = ObjectId()
        if 'creator' not in self.__dict__:
            self.creator = constants.DEFAULT_CREATOR
        if 'createdTime' not in self.__dict__:
            self.createdTime = datetime.now()
        if 'lastModified' not in self.__dict__:
            self.lastModified = datetime.now()

    def generic(self):
        """ A shallow copy of the __dict__, 
        and make neccessary conversion as needed"""
        result = {}
        result.update(self.__dict__)
        del result['_id']
        result['lastModified'] = datetime.now()
        self.appendType(result)
        return result
        
    def save(self, **kwargs):
        logger.warning('no store for abstract MONKObject')
        return None
        
    @classmethod
    def appendType(cls, result):
        result[constants.MONK_TYPE] = cls.__name__

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
        
    def decode(self, generic):
        return self.factory[generic[constants.MONK_TYPE]](generic)

    def clone(self, obj, modification = {}):
        try:
            generic = obj.generic()
            generic['_id'] = ObjectId()
            generic['creator'] = constants.DEFAULT_CREATOR
            generic['createdTime'] = datetime.now()
            generic['lastModified'] = datetime.now()            
            generic.update(modification)
            return self.decode(generic)
        except Exception as e:
            logger.warning('can not clone the object {0}'.format(e.message))
            return None

monkFactory = MONKObjectFactory()

def register(MONKObjectClass):
    monkFactory.register(MONKObjectClass)
    