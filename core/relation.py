# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 07:27:15 2013

@author: xm
"""
import pyximport; pyximport.install(setup_args={"include_dirs":'.'}, reload_support=True)
from pymonk.math.flexible_vector import matching, difference
from pymonk.core.entity import Entity
from pymonk.core.monk import *
from pymonk.utils.utils import GetIds

class Relation(Entity):
    def __restore__(self):
        super(Relation, self).__restore__()
        self._arguments = loadOrCreateAll(entityStore, self._arguments)
    
    def __defaults__(self):
        super(Relation, self).__defaults__()
        self._arguments = []
    
    def generic(self):
        result = super(Relation, self).generic()
        result["_type"].append("Relation")
        result["_arguments"] = GetIds(self._arguments)
        return result
    
    def arity(self):
        return len(self._arguments)

class DifferenceRelation(Relation):
    def __restore__(self):
        super(DifferenceRelation, self).__restore__()
        if '_validate' in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            relation._features = difference(ent1._features, ent2._features)
            del self.__dict__['validate']
    
    def generic(self):
        result = super(DifferenceRelation, self).generic()
        result['_type'].append('DifferenceRelation')
    
class MatchingRelation(Relation):
    def __restore__(self):
        super(MatchingRelation, self).__restore__()
        if '_validate' in self.__dict__:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            relation._features = matching(ent1._features, ent2._features)
            del self.__dict__['validate']
    
    def generic(self):
        result = super(MatchingRelation, self).generic()
        result['_type'].append('MatchingRelation')
    
monkObjectFactory.register("Relation", Relation.create)
monkObjectFactory.register("DifferenceRelation", DifferenceRelation.create)
monkObjectFactory.register("MatchingRelation", MatchingRelation.create)