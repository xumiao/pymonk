# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 07:27:15 2013

@author: xm
"""
from ..math.flexible_vector import matching, difference
import base,crane
import constants
from entity import Entity

class Relation(Entity):

    def __restore__(self):
        super(Relation, self).__restore__()
        if constants.ARGUMENTS not in self.__dict__:
            self._arguments = []
        else:
            self._arguments = crane.entityStore.load_or_create_all(self._arguments)

    def generic(self):
        result = super(Relation, self).generic()
        result[constants.ARGUMENTS] = [x._id for x in self._arguments]
        return result

    def save(self, **kwargs):
        if kwargs and kwargs.has_key('fields'):
            fields = kwargs['fields']
        else:
            fields = {constants.FEATURES: self._features.generic(),
                      constants.RAWS: self._raws,
                      constants.ARGUMENTS: [x._id for x in self._arguments]}
        crane.entityStore.update_one_in_fields(self, fields)
        
    def arity(self):
        return len(self._arguments)


class DifferenceRelation(Relation):

    def __restore__(self):
        super(DifferenceRelation, self).__restore__()
        if constants.FEATURES not in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features = difference(ent1._features, ent2._features)

class MatchingRelation(Relation):

    def __restore__(self):
        super(MatchingRelation, self).__restore__()
        if constants.FEATURES in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features = matching(ent1._features, ent2._features)
        
base.register(Relation)
base.register(DifferenceRelation)
base.register(MatchingRelation)
