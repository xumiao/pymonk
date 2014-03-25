# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:22 2013
The general object used in MONK
@author: xm
"""
from ..math.flexible_vector import FlexibleVector
from datetime import datetime
import base, crane
import constants

class Entity(base.MONKObject):

    def __restore__(self):
        super(Entity, self).__restore__()
        if constants.FEATURES in self.__dict__:
            self._features = FlexibleVector(generic=self._features)
        else:
            self._features = FlexibleVector()
        if constants.RAWS not in self.__dict__:
            self._raws = {}

    def generic(self):
        result = {}
        result['creator'] = self.creator
        result['createdTime'] = self.createdTime
        result['lastModified'] = datetime.now()
        result[constants.FEATURES] = self._features.generic()
        result[constants.RAWS] = self._raws
        return result
    
    def save(self,**kwargs):
        if kwargs and kwargs.has_key('fields'):
            fields = kwargs['fields']
        else:
            fields = self.generic()
        crane.entityStore.update_one_in_fields(self, fields)
        
    def __contains__(self, key):
        return key in self._features or key in self._raws

    def __setitem__(self, key, value):
        self._features[key] = value

    def __getitem__(self, key):
        return self._features.find(key)

    def getRaw(self, rawKey):
        if rawKey in self._raws:
            return self._raws[rawKey]
        else:
            return constants.DEFAULT_EMPTY

    def setRaw(self, rawKey, rawValue):
        if isinstance(rawKey, basestring):
            self._raws[
                rawKey.replace('.', '\uff0e').replace('$', '\uff04')] = rawValue

base.register(Entity)
