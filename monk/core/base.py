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
    NAME            = 'name'
    CREATOR         = 'creator'
    CREATED_TIME    = 'createdTime'
    LAST_MODIFIED   = 'lastModified'
    store = None
    
    def __init__(self, generic=None):
        self.__default__()
        
        if generic:
            try:
                self.__dict__.update({k:v for k,v in generic.iteritems() if ((k is not None) and (v is not None))})
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
        self.name = cons.DEFAULT_EMPTY
        self.creator = cons.DEFAULT_CREATOR
        self.createdTime = datetime.now()
        self.lastModified = datetime.now()
        
    def _hasattr(self, key):
        return key in self.__dict__
        
    def _setattr(self, key, value, converter=None):
        if value is not None:
            if converter:
                try:
                    self.__dict__[key] = converter(value)
                except Exception as e:
                    logger.error('can not set attribute {}:{}'.format(key, value))
                    logger.error('converter failed')
                    logger.debug(e.message)
            else:
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
        self.lastModified = datetime.now()
        result[self.LAST_MODIFIED] = self.lastModified
        del result[self.ID]
        return result
    
    def save(self):
        if self.store:
            self.store.update_one_in_fields(self, self.generic())
        else:
            logger.warning('no store for abstract MONKObject')
    
    def signature(self):
        return {self.NAME:self.name, self.CREATOR:self.creator}
        
    def delete(self, deep=False):
        if self.store:
            return self.store.delete_by_id(self._id)
        else:
            logger.warning('no store for abstract MONKObject')
            return False
            
    def clone(self, userName):
        """ Reuse the object in store """
        if self.store:
            obj = self.store.load_or_create({'name':self.name, 'creator':userName})
            if obj:
                return obj
                
        try:
            obj = self.create()
            for key in self._allattr([self.ID, self.CREATOR, self.CREATED_TIME, self.LAST_MODIFIED]):
                obj._setattr(key, self._getattr(key))
            obj.creator = userName
            return obj
        except Exception as e:
            logger.error(e.message)
            logger.error('can not clone {0}'.format(self.generic()))
            return None
    
    def update_fields(self, fields={}):
        if fields:
            self.store.update_one_in_fields(self, fields)
            
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
            return self.factory[generic[MONKObject.MONK_TYPE]](generic)
        except Exception as e:
            logger.error(e.message)
            logger.error('can not decode {0}'.format(generic))

monkFactory = MONKObjectFactory()

def register(MONKObjectClass):
    monkFactory.register(MONKObjectClass)

register(MONKObject)