# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:19 2013
The project object
@author: xm
"""
import logging
import constants as cons
from datetime import datetime
from bson.objectid import ObjectId
logger = logging.getLogger("monk.base")

class MONKObject(object):

    def __init__(self, generic=None):
        if generic:
            try:
                self.__dict__.update(generic)
            except Exception as e:
                logger.debug('trying to deserialize {0}'.format(generic))
                logger.warning('deserializatin failed. {0}'.format(e.message))
                logger.warning('defaulting')
        try:
            self.__restore__()
        except Exception as e:
            logger.warning('restoration failed. {0}'.format(e.message))
            logger.debug('generic {0}'.format(generic))

    def __restore__(self):
        self._default(cons.ID, ObjectId())
        self._default(cons.CREATOR, cons.DEFAULT_CREATOR)
        self._default(cons.CREATED_TIME, datetime.now())
        self._default(cons.LAST_MODIFIED, datetime.now())
    
    def _default(self, key, value):
        if key not in self.__dict__:
            self.__dict__[key] = value
            
    def generic(self):
        """ A shallow copy of the __dict__, 
        and make neccessary conversion as needed"""
        result = {}
        result.update(self.__dict__)
        del result[cons.ID]
        result[cons.LAST_MODIFIED] = datetime.now()
        self.appendType(result)
        return result
        
    def save(self, **kwargs):
        logger.warning('no store for abstract MONKObject')
        return None
        
    @classmethod
    def appendType(cls, result):
        result[cons.MONK_TYPE] = cls.__name__

    @classmethod
    def create(cls, generic):
        return cls(generic)


class MONKObjectFactory(object):

    def __init__(self):
        self.factory = {}

    def register(self, MONKObjectClass):
        self.factory[MONKObjectClass.__name__] = MONKObjectClass.create

    def find(self, name):
        return [key for key in self.factory.iterkeys() if key.find(name) >= 0]
        
    def decode(self, generic):
        return self.factory[generic[cons.MONK_TYPE]](generic)

    def clone(self, obj, modification = {}):
        try:
            generic = obj.generic()
            generic[cons.ID] = ObjectId()
            generic[cons.CREATOR] = cons.DEFAULT_CREATOR
            generic[cons.CREATED_TIME] = datetime.now()
            generic[cons.LAST_MODIFIED] = datetime.now()            
            generic.update(modification)
            return self.decode(generic)
        except Exception as e:
            logger.warning('can not clone the object {0}'.format(e.message))
            return None

monkFactory = MONKObjectFactory()

def register(MONKObjectClass):
    monkFactory.register(MONKObjectClass)

register(MONKObject)