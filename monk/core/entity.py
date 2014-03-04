# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:22 2013
The general object used in MONK
@author: xm
"""
from monk.math.flexible_vector import FlexibleVector
from monk.core.monk import *

__FEATURES = '_features'
__RAWS = '_raws'


class Entity(MONKObject):

    def __restore__(self):
        super(Entity, self).__restore__()
        if __FEATURES in self.__dict__:
            self._features = FlexibleVector(generic=self._features)
        else:
            self._features = FlexibleVector()
        if __RAWS not in self.__dict__:
            self._raws = {}

    def __defaults__(self):
        super(Entity, self).__defaults__()
        self._raws = {}
        self._features = FlexibleVector()

    def generic(self):
        result = super(Entity, self).generic()
        self.appendType(result)
        result[__FEATURES] = self._features.generic()
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
            return __DEFAULT_EMPTY

    def setRaw(self, rawKey, rawValue):
        if isinstance(rawKey, basestring):
            self._raws[
                rawKey.replace('.', '\uff0e').replace('$', '\uff04')] = rawValue

monkFactory.register(Entity)
