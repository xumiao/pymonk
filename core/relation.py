# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 07:27:15 2013

@author: xm
"""
from pymonk.math.flexible_vector import matching, difference
from pymonk.core.monk import *
from pymonk.core.entity import Entity

__ARGUMENTS = '_arguments'
__VALIDATE = '_validate'

class Relation(Entity):
    def __restore__(self):
        super(Relation, self).__restore__()
        self._arguments = monkFactory.load_or_create_all(entityStore, self._arguments)
    
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
    
monkFactory.register("Relation", Relation.create)
monkFactory.register("DifferenceRelation", DifferenceRelation.create)
monkFactory.register("MatchingRelation", MatchingRelation.create)