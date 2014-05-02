# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:22 2013
The general object used in MONK
@author: xm
"""
from ..math.flexible_vector import FlexibleVector
import base, crane
import constants as cons

class Entity(base.MONKObject):

    def __restore__(self):
        super(Entity, self).__restore__()
        self._default(cons.FEATURES, [])
        self._default(cons.RAWS, {})
        self._features = FlexibleVector(generic=self._features)
        
    def generic(self):
        result = super(Entity, self).generic()
        result[cons.FEATURES] = self._features.generic()
        return result
    
    def save(self,**kwargs):
        if kwargs and 'fields' in kwargs:
            fields = kwargs['fields']
        else:
            fields = {cons.FEATURES:self._features.generic(),
                      cons.RAWS:self._raws}
        crane.entityStore.update_one_in_fields(self, fields)
        
    def __contains__(self, key):
        return key in self._features or key in self._raws

    def __setitem__(self, key, value):
        self._features[key] = value

    def __getitem__(self, key):
        return self._features[key]

    def getRaw(self, rawKey):
        if rawKey in self._raws:
            return self._raws[rawKey]
        else:
            return cons.DEFAULT_EMPTY

    def setRaw(self, rawKey, rawValue):
        if isinstance(rawKey, basestring):
            self._raws[rawKey.replace('.', '\uff0e').replace('$', '\uff04')] = rawValue

    def set_value(self, key, value):
        if value != 0 and key not in self._features:
            self._features[key] = value
            crane.entityStore.push_one_in_fields(self, {cons.FEATURES:(key,value)})
        return value
        
base.register(Entity)
