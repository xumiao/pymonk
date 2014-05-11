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
    ID              = '_id' # for mongodb
    MONK_TYPE       = 'monkType'
    CREATOR         = 'creator'
    CREATED_TIME    = 'createdTime'
    LAST_MODIFIED   = 'lastModified'
    store = None
    
    def __init__(self, generic=None):
        self.__default__()
        
        if generic:
            try:
                self.__dict__.update(generic)
            except Exception as e:
                logger.debug('trying to deserialize {0}'.format(generic))
                logger.warning('deserializatin failed. {0}'.format(e.message))
            
        try:
            self.__restore__()
        except Exception as e:
            logger.warning('restoration failed. {0}'.format(e.message))
            logger.debug('generic {0}'.format(generic))

    def __restore__(self):
        pass
    
    def __default__(self):
        self._id = ObjectId()
        self.monkType = self.get_type_name()
        self.creator = cons.DEFAULT_CREATOR
        self.createdTime = datetime.now()
        self.lastModified = datetime.now()
        
    def _hasattr(self, key):
        return key in self.__dict__
        
    def _setattr(self, key, value):
        self.__dict__[key] = value
    
    def _getattr(self, key, default=None):
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            return default

    def _allattr(self, exclusive=[]):
        return set(self.__dict__.keys()).difference(exclusive)
        
    def generic(self):
        """ A shallow copy of the __dict__, 
        and make neccessary conversion as needed"""
        result = {}
        result.update(self.__dict__)
        result[self.LAST_MODIFIED] = datetime.now()
        return result
    
    def save(self, **kwargs):
        if self.store:
            self.store.update_one_in_fields(self, self.generic())
        else:
            logger.warning('no store for abstract MONKObject')
    
    def delete(self):
        if self.store:
            return self.store.delete_one_by_id(self._id)
        else:
            logger.warning('no store for abstract MONKObject')
            return False
            
    def clone(self, user):
        """ Reuse the object in store """
        if self.store:
            obj = self.store.load_one_by_name_user(self.name, user)
            if obj:
                return obj
                
        try:
            obj = self.create()
            for key in self._allattr([self.ID, self.CREATOR, self.CREATED_TIME, self.LAST_MODIFIED]):
                obj._setattr(key, self._getattr(key))
            obj.creator = user
            return obj
        except Exception as e:
            logger.error(e.message)
            logger.error('can not clone {0}'.format(self.generic()))
            return None
        
    @classmethod
    def get_type_name(cls):
        return cls.__name__

    @classmethod
    def create(cls, generic=None):
        return cls(generic)


class MONKObjectFactory(object):

    def __init__(self):
        self.factory = {}

    def register(self, MONKObjectClass):
        self.factory[MONKObjectClass.__name__] = MONKObjectClass.create

    def find(self, name):
        return [key for key in self.factory.iterkeys() if key.find(name) >= 0]
        
    def decode(self, generic):
        try:
            return self.factory[generic[cons.MONK_TYPE]](generic)
        except Exception as e:
            logger.error(e.message)
            logger.error('can not decode {0}'.format(generic))

monkFactory = MONKObjectFactory()

def register(MONKObjectClass):
    monkFactory.register(MONKObjectClass)

register(MONKObject)