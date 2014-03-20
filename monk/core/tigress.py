# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:53:08 2013
A supervisor looks for signals and decides the training strategy
@author: xm
"""

from base import MONKObject, monkFactory
import re

class Tigress(MONKObject):
    """
    The base class for Tigress, and does nothing
    """
    
    def __restore__(self):
        super(Tigress, self).__restore__()
        if "name" not in self.__dict__:
            self.name = 'tigress'
        if "description" not in self.__dict__:
            self.description = ''
        if "pCuriosity" not in self.__dict__:
            self.pCuriosity = 0.0
        if "confusionMatrix" not in self.__dict__:
            self.confusionMatrix = {}
        if "costs" not in self.__dict__:
            self.costs = {}

    def __defaults__(self):
        super(Tigress, self).__defaults__()
        self.pCuriosity = 0.0
        self.confusionMatrix = {}

    def generic(self):
        result = super(Tigress, self).generic()
        self.appendType(result)
        return result
        
    def accuracy(self, partition_id, target):
        return self.confusionMatrix[partition_id][target]
        
    def supervise(self, turtle, partition_id, entity):
        pass
    


class PatternTigress(Tigress):
    """
    Find patterns for the targets. 
    """

    def __restore__(self):
        super(PatternTigress, self).__restore__()
        if 'patterns' not in self.__dict__:
            self.patterns = {}
        if 'fields' not in self.__dict__:
            self.fields = []
        self.p = {re.compile(pattern) : target for target, pattern in self.patterns.iteritems()}

    def __defaults__(self):
        super(PatternTigress, self).__defaults__()
        self.patterns = {}
        self.p = {}

    def generic(self):
        result = super(PatternTigress, self).generic()
        self.appendType(result)
        return result

    def supervise(self, turtle, partition_id, entity):
        combinedField = ' . '.join([str, self.fields])
        pandas = turtle.pandas
        for r, t in self.p:
            if r.search(combinedField):
                cost = self.costs[partition_id][t]
                ys = turtle.mapping[t]
                for i in xrange(len(ys)):
                    pandas[i].mantis.set_data(partition_id, 
                                              entity._features, 
                                              ys[i], 
                                              cost)
                # found the target
                return
        # no pattern found, looking for the _default bit
        
class SelfTigress(Tigress):

    def generic(self):
        result = super(SelfTigress, self).generic()
        self.appendType(result)
        return result

class SPNTigress(Tigress):

    def generic(self):
        result = super(SPNTigress, self).generic()
        self.appendType(result)
        return result
        
class LexiconTigress(Tigress):

    def generic(self):
        result = super(LexiconTigress, self).generic()
        self.appendType(result)
        return result
        
class ActiveTigress(Tigress):

    def generic(self):
        result = super(ActiveTigress, self).generic()
        self.appendType(result)
        return result
        
class CoTigress(Tigress):

    def generic(self):
        result = super(CoTigress, self).generic()
        self.appendType(result)
        return result
        
monkFactory.register(Tigress)
monkFactory.register(PatternTigress)
monkFactory.register(SelfTigress)
monkFactory.register(SPNTigress)
monkFactory.register(LexiconTigress)
monkFactory.register(ActiveTigress)
monkFactory.register(CoTigress)
