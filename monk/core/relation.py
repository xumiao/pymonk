# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 07:27:15 2013

@author: xm
"""
from ..math.flexible_vector import matching, difference
import base
from crane import entityStore
from entity import Entity

__ARGUMENTS = '_arguments'
__VALIDATE = '_validate'


class Relation(Entity):

    def __restore__(self):
        super(Relation, self).__restore__()
        self._arguments = entityStore.load_or_create_all(self._arguments)

    def __defaults__(self):
        super(Relation, self).__defaults__()
        self._arguments = []

    def generic(self):
        result = super(Relation, self).generic()
        self.appendType(result)
        result[__ARGUMENTS] = map(lambda x: x._id, self._arguments)
        return result

    def arity(self):
        return len(self._arguments)


class DifferenceRelation(Relation):

    def __restore__(self):
        super(DifferenceRelation, self).__restore__()
        if __VALIDATE in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features = difference(ent1._features, ent2._features)
            del self.__dict__[__VALIDATE]

    def generic(self):
        result = super(DifferenceRelation, self).generic()
        self.appendType(result)
        return result

class MatchingRelation(Relation):

    def __restore__(self):
        super(MatchingRelation, self).__restore__()
        if __VALIDATE in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features = matching(ent1._features, ent2._features)
            del self.__dict__[__VALIDATE]

    def generic(self):
        result = super(MatchingRelation, self).generic()
        self.appendType(result)
        return result
        
base.register(Relation)
base.register(DifferenceRelation)
base.register(MatchingRelation)
