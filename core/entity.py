# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:22 2013
The general object used in MONK
@author: xm
"""
import pyximport; pyximport.install(setup_args={"include_dirs":'.', 'options': { 'build_ext': { 'compiler': 'mingw32' }}}, reload_support=True)
from pymonk.math.flexible_vector import FlexibleVector
from pymonk.core.monk import MONKObject, monkObjectFactory

class Entity(MONKObject):
    def __restore__(self):
        super(Entity, self).__restore__()
        if '_features' in self.__dict__:
            f = FlexibleVector()
            f.update(self._features)
            self._features = f
        else:
            self._features = FlexibleVector()
        if '_raws' not in self.__dict__:
            self._raws = {}
        
    def __defaults__(self):
        super(Entity, self).__defaults__()
        self._raws = {}
        self._features = FlexibleVector()
        
    def generic(self):
        result = super(Entity, self).generic()
        result["_type"].append("Entity")
        result["_features"] = self._features.generic()
        return result
    
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
            return ""
    
    def setRaw(self, rawKey, rawValue):
        if isinstance(rawKey, basestring):
            self._raws[rawKey.replace('.', '\uff0e').replace('$', '\uff04')] = rawValue

monkObjectFactory.register("Entity", Entity.create)