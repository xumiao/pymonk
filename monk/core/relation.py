# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 07:27:15 2013

@author: xm
"""
import base, crane
from entity import Entity
import logging
logger = logging.getLogger('monk.relation')

class Relation(Entity):
    ARGUMENTS = '_arguments'
    
    def __default__(self):
        super(Relation, self).__default__()
        self._arguments = []
        
    def __restore__(self):
        super(Relation, self).__restore__()
        self._arguments = crane.entityStore.load_or_create_all(self._arguments)
    
    def set_argument(self, position, entity):
        self._arguments[position] = entity
        
    def generic(self):
        result = super(Relation, self).generic()
        result[self.ARGUMENTS] = [x._id for x in self._arguments]
        return result

    def save(self):
        fields = {self.FEATURES: self._features.generic(),
                  self.RAWS: self._raws,
                  self.ARGUMENTS: [x._id for x in self._arguments]}
        crane.entityStore.update_one_in_fields(self, fields)
        
    def arity(self):
        return len(self._arguments)
        
    def compute(self):
        pass

class DifferenceRelation(Relation):

    def compute(self):
        try:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features.copyUpdate(ent1._features)
            self._features.difference(ent2._features)
        except Exception as e:
            logger.error(e.message)
            logger.error('failed to compute the difference relation')

class MatchingRelation(Relation):

    def compute(self):
        try:
            ent1 = self._arguments[0]
            ent2 = self._arguments[1]
            self._features.copyUpdate(ent1._features)
            self._features.matching(ent2._features)
        except Exception as e:
            logger.error(e.message)
            logger.error('failed to compute the matching relation')
        
base.register(Relation)
base.register(DifferenceRelation)
base.register(MatchingRelation)
