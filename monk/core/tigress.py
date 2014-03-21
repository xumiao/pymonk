# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:53:08 2013
A supervisor looks for signals and decides the training strategy
@author: xm
"""

import base 
import re
from itertools import izip

class Tigress(base.MONKObject):
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
    
    def measure(self, partition_id, entity, predicted):
        cm = self.confusionMatrix[partition_id]
        for target in self.retrieve_target(entity):
            cm[target][predicted] += 1
    
    def retrieve_target(self, entity):
        return () # an empty iterator
    
    def accuracy(self, partition_id, target):
        return self.confusionMatrix[partition_id][target]
        
    def supervise(self, turtle, partition_id, entity):
        pass
    


class PatternTigress(Tigress):
    """
    Find patterns for the targets. 
    Fields:
        patterns : regular expression based patterns for each target defined
        fields   : fields for searching targets
        mutualExclusive : only the first found pattern will be set as ground truth
        defaulting : add as negative examples if no pattern found
    """

    def __restore__(self):
        super(PatternTigress, self).__restore__()
        if 'patterns' not in self.__dict__:
            self.patterns = {}
        if 'fields' not in self.__dict__:
            self.fields = []
        self.p = {re.compile(pattern) : target for target, pattern in self.patterns.iteritems()}
        if 'mutualExclusive' in self.__dict__:
            self.isMutualExclusive = True
        else:
            self.isMutualExclusive = False
        if 'defaulting' in self.__dict__:
            self.isDefaulting = True
        else:
            self.isDefaulting = False

    def __defaults__(self):
        super(PatternTigress, self).__defaults__()
        self.patterns = {}
        self.p = {}
        self.isMutualExclusive = False
        self.isDefaulting = False

    def generic(self):
        result = super(PatternTigress, self).generic()
        self.appendType(result)
        del result['isMutualExclusive']
        del result['isDefaulting']
        return result

    def retrieve_target(self, entity):
        combinedField = ' . '.join([str, self.fields])
        return (t for r, t in self.p if r.search(combinedField))
        
    def supervise(self, turtle, partition_id, entity):
        pandas = turtle.pandas
        x = entity._features
        for t in self.retrieve_target(entity):
            cost = self.costs[partition_id][t]
            ys = turtle.mapping[t]
            [panda.mantis.set_data(partition_id, x, y, cost) for panda, y in izip(pandas, ys)]
            if self.isMutualExclusive:
                return

        if self.isDefaulting:
            # no pattern found, add all negative
            mincost = min(self.costs[partition_id].itervalues())
            [panda.mantis.set_data(partition_id, x, -1, mincost) for panda in pandas]
        
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
        
base.register(Tigress)
base.register(PatternTigress)
base.register(SelfTigress)
base.register(SPNTigress)
base.register(LexiconTigress)
base.register(ActiveTigress)
base.register(CoTigress)
