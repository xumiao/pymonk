# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:53:08 2013
A supervisor looks for signals and decides the training strategy
@author: xm
"""

import base,crane
import re
from itertools import izip
import logging
logger = logging.getLogger('monk.tigress')

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
    
    def generic(self):
        result = super(Tigress, self).generic()
        try:
            del result['confusionMatrix']
        except Exception as e:
            logger.warning('deleting solvers failed {0}'.format(e.message))
        return result
    
    def save(self, **kwargs):
        if kwargs and kwargs.has_key('partition_id'):
            self.save_one(kwargs['partition_id'])
        else:
            crane.tigressStore.update_one_in_fields(self, self.generic())
            
    def has_partition(self, partition_id):
        return partition_id in self.confusionMatrix
        
    def measure(self, partition_id, entity, predicted):
        cm = self.confusionMatrix[partition_id]
        for target in self.retrieve_target(entity):
            if target not in cm:
                cm[target] = {predicted:1}
            elif predicted not in cm[target]:
                cm[target][predicted] = 1
            else:
                cm[target][predicted] += 1
        if '__total__' not in cm:
            cm['__total__'] = 0
        else:
            cm['__total__'] += 1
    
    def load_one(self, partition_id):
        if partition_id not in self.confusionMatrix:
            field = 'confusionMatrix.{0}'.format(partition_id)
            tg = crane.tigressStore.load_one_in_fields(self, [field])
            try:
                self.confusionMatrix[partition_id] = tg['confusionMatrix'][partition_id]
            except:
                self.confusionMatrix[partition_id] = {}
                
    def save_one(self, partition_id):
        if partition_id in self.confusionMatrix:
            field = 'confusionMatrix.{0}'.format(partition_id)
            crane.tigressStore.update_one_in_fields(self, {field:self.confusionMatrix[partition_id]})
            
    def retrieve_target(self, entity):
        return () # an empty iterator
    
    def accuracy(self, partition_id, target):
        try:
            return self.confusionMatrix[partition_id][target]
        except:
            logger.warning('target {0} not found in confusion matrix'.format(target))
            return {}
        
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
        if 'mutualExclusive' not in self.__dict__:
            self.mutualExclusive = False
        if 'defaulting' not in self.__dict__:
            self.defaulting = False

    def generic(self):
        result = super(PatternTigress, self).generic()
        del result['p']
        return result

    def retrieve_target(self, entity):
        combinedField = ' . '.join([str, self.fields])
        return (t for r, t in self.p if r.search(combinedField))
        
    def supervise(self, turtle, partition_id, entity):
        pandas = turtle.pandas
        x = entity._features
        for t in self.retrieve_target(entity):
            cost = self.costs[t]
            ys = turtle.mapping[t]
            [panda.mantis.set_data(partition_id, x, y, cost) for panda, y in izip(pandas, ys)]
            if self.mutualExclusive:
                return

        if self.defaulting:
            # no pattern found, add all negative
            mincost = min(self.costs.itervalues())
            [panda.mantis.set_data(partition_id, x, -1, mincost) for panda in pandas]
        
class SelfTigress(Tigress):
    pass
class SPNTigress(Tigress):
    pass        
class LexiconTigress(Tigress):
    pass        
class ActiveTigress(Tigress):
    pass        
class CoTigress(Tigress):
    pass

base.register(Tigress)
base.register(PatternTigress)
base.register(SelfTigress)
base.register(SPNTigress)
base.register(LexiconTigress)
base.register(ActiveTigress)
base.register(CoTigress)
