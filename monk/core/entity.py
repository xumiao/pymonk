# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:22 2013
The general object used in MONK
@author: xm
"""
from ..math.flexible_vector import FlexibleVector
import base, crane
import constants as cons
import logging
logger = logging.getLogger('monk.entity')

class Entity(base.MONKObject):
    FEATURES = '_features'
    RAWS     = '_raws'
    
    def __default__(self):
        super(Entity, self).__default__()
        self._features = []
        self._raws = dict()
        
    def __restore__(self):
        super(Entity, self).__restore__()
        self._features = FlexibleVector(generic=self._features)
        
    def generic(self):
        result = super(Entity, self).generic()
        result[self.FEATURES] = self._features.generic()
        return result
    
    def clone(self, userName):
        logger.error('entity can not be cloned')
        return None
        
    def save(self):
        fields = {self.FEATURES:self._features.generic(),
                  self.RAWS:self._raws}
        crane.entityStore.update_one_in_fields(self, fields)
        
    def __contains__(self, key):
        return key in self._features or key in self._raws

    def __setitem__(self, key, value):
        self._features[key] = value

    def __getitem__(self, key):
        return self._features[key]

    def get_raw(self, rawKey, default=0):
        if rawKey in self._raws:
            return self._raws[rawKey]
        else:
            return default

    def set_raw(self, rawKey, rawValue):
        if isinstance(rawKey, basestring):
            self._raws[rawKey.replace('.', '\uff0e').replace('$', '\uff04')] = rawValue

    def set_value(self, key, value):
        if value != 0 and key not in self._features:
            self._features[key] = value
            crane.entityStore.push_one_in_fields(self, {self.FEATURES:(key,value)})
        return value
        
base.register(Entity)
