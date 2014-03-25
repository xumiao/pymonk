# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 07:27:15 2013

@author: xm
"""
from ..math.flexible_vector import matching, difference
import base
import constants
from crane import entityStore
from entity import Entity

class Relation(Entity):

    def __restore__(self):
        super(Relation, self).__restore__()
        if '_arguments' not in self.__dict__:
            self._arguments = []
        else:
            self._arguments = entityStore.load_or_create_all(self._arguments)

    def generic(self):
        result = super(Relation, self).generic()
        result[constants.ARGUMENTS] = [x._id for x in self._arguments]
        return result

    def arity(self):
        return len(self._arguments)


class DifferenceRelation(Relation):

    def __restore__(self):
        super(DifferenceRelation, self).__restore__()
        if constants.VALIDATE in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features = difference(ent1._features, ent2._features)
            del self.__dict__[constants.VALIDATE]

class MatchingRelation(Relation):

    def __restore__(self):
        super(MatchingRelation, self).__restore__()
        if constants.VALIDATE in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features = matching(ent1._features, ent2._features)
            del self.__dict__[constants.VALIDATE]
        
base.register(Relation)
base.register(DifferenceRelation)
base.register(MatchingRelation)
