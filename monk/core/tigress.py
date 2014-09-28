# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:53:08 2013
A supervisor looks for signals and decides the training strategy
@author: xm
"""

import base,crane
import re
from itertools import izip
import monk.utils.utils as utils
import constants as cons
import logging
logger = logging.getLogger('monk.tigress')

class Tigress(base.MONKObject):
    """
    The base class for Tigress, and does nothing
    """
    FNAME                = 'name'
    FDESCRIPTION         = 'description'
    FCURIOSITY           = 'curiosity'
    FCONFUSION_MATRIX    = 'confusionMatrix'
    FCOSTS               = 'costs'
    FDEFAULT_COST        = 'defaultCost'
    FDISPLAY_TEXT_FIELDS = 'displayTextFields'
    FDISPLAY_IMAGE_FIELD = 'displayImageField'
    FACTIVE_BATCH_SIZE   = 'activeBatchSize'
    FTOTAL               = 'total'
    store = crane.tigressStore
    
    def __default__(self):
        super(Tigress, self).__default__()
        self.name = cons.DEFAULT_EMPTY
        self.description = cons.DEFAULT_EMPTY
        self.curiosity = 0.0
        self.confusionMatrix = {}
        self.costs = {}
        self.defaultCost = 1.0
        self.displayTextFields = []
        self.displayImageField = None
        self.activeBatchSize = 10
        self.total = 1e-8

    def retrieve_target(self, entity):
        return () # an empty iterator
    
    def measure(self, entity, predicted):
        cm = self.confusionMatrix
        for target in self.retrieve_target(entity):
            if target not in cm:
                cm[target] = {predicted:1}
            elif predicted not in cm[target]:
                cm[target][predicted] = 1
            else:
                cm[target][predicted] += 1
        self.total += 1

    def accuracy(self, target):
        try:
            return self.confusionMatrix[target]
        except:
            logger.warning('target {0} not found in confusion matrix'.format(target))
            return {}
        
    def supervise(self, turtle, entity):
        return True
    

class PatternTigress(Tigress):
    """
    Find patterns for the targets. 
    Fields:
        patterns : regular expression based patterns for each target defined
        fields   : fields for searching targets
        mutualExclusive : only the first found pattern will be set as ground truth
        defaulting : add as negative examples if no pattern found
    """
    FPATTERNS         = 'patterns'
    FFIELDS           = 'fields'
    FMUTUAL_EXCLUSIVE = 'mutualExclusive'
    FDEFAULTING       = 'defaulting'

    def __default__(self):
        super(PatternTigress, self).__default__()
        self.patterns = {}
        self.fields = []
        self.mutualExclusive = False
        self.defaulting = False
        
    def __restore__(self):
        super(PatternTigress, self).__restore__()
        self.p = {re.compile(pattern) : target for target, pattern in self.patterns.iteritems()}

    def generic(self):
        result = super(PatternTigress, self).generic()
        del result['p']
        return result

    def clone(self, userName):
        obj = super(PatternTigress, self).clone(userName)
        obj.patterns = dict(self.patterns)
        obj.p = {re.compile(pattern) : target for target, pattern in self.patterns.iteritems()}
        obj.fields = list(self.fields)
        return obj
        
    def retrieve_target(self, entity):
        combinedField = ' . '.join([utils.translate(entity._getattr(field, ""), ' . ') for field in self.fields])
        logger.debug('combinedField {0}'.format(combinedField))
        result = [t for r, t in self.p.iteritems() if r.search(combinedField)]
        return result
    
    def _supervise(self, turtle, entity, tags):
        for t in tags:
            cost = self.costs.get(t, self.defaultCost)
            ys = turtle.mapping[t]
            [panda.add_data(entity, y, cost) for panda, y in izip(turtle.pandas, ys)]
            if self.mutualExclusive:
                return True

        if self.defaulting and not tags:
            # no pattern found, add all negative
            [panda.add_data(entity, -1, self.defaultCost) for panda in turtle.pandas]
        
    def supervise(self, turtle, entity=None):
        if entity:
            self._supervise(turtle, entity, self.retrieve_target(entity))
        else:
            if not self.fields:
                logger.error('no target fields have been given for the turtle')
                return False
            #TODO: make the rendering and querying as web-services instead of console   
            toExit = False
            rawTags = self.patterns.values()
            rawTags = dict(zip(range(len(rawTags)), rawTags))
            tags = ' '.join(('.'.join([str(it[0]),str(it[1])]) for it in rawTags.iteritems()))
            if self.mutualExclusive:
                display = 'Choose ONE tag from [{0}]\n'.format(tags)
            else:
                display = 'Choose Multiple tags from [{0}]\n'.format(tags)
            crane.entityStore.set_collection_name(turtle.entityCollectionName)
            while not toExit:
                # load unseen entities
                ents = crane.entityStore.load_all_in_ids({field : {'$exists' : False} for field in self.fields}, skip=0, num=self.activeBatchSize)
                ents = crane.entityStore.load_all_by_ids([ent['_id'] for ent in ents])
                if ents:
                    for ent in ents:
                        utils.show(ent, fields=self.displayTextFields, imgField=self.displayImageField)
                        tags = raw_input(display)
                        if tags == "bye":
                            toExit = True
                            break
                        else:
                            tags = tags.split(' ')
                            try:
                                tags = [rawTags[int(t)] for t in tags]
                            except:
                                pass
                            setattr(ent, self.fields[0], tags)
                            ent.save(fields={self.fields[0]:tags})
                            self._supervise(turtle, ent, tags)
                    logger.info('training')
                    turtle.train()
                else:
                    #TODO: load uncertain entities
                    toExit = True
            logger.info('active training stopped')
        return True

class MultiLabelTigress(PatternTigress):
    """
    Find independent patterns for the targets. 
    Fields:
        patterns : regular expression based patterns for each target defined
        fields   : fields for searching targets
    """
    def measure(self, entity, predicted):
        cm = self.confusionMatrix
        target = tuple(self.retrieve_target(entity))
        predicted = tuple(predicted)
        if target not in cm:
            cm[target] = {predicted:1}
        elif predicted not in cm[target]:
            cm[target][predicted] = 1
        else:
            cm[target][predicted] += 1
        self.total += 1
        
    def accuracy(self, target):
        try:
            return self.confusionMatrix[target]
        except:
            logger.warning('target {0} not found in confusion matrix'.format(target))
            return {}

    def _supervise(self, turtle, entity, tags):
        targets = set(tags)
        [panda.add_data(entity, 1, self.costs.get(panda.name, self.defaultCost))
         for panda in turtle.pandas if panda.name in targets]
        [panda.add_data(entity, -1, self.costs.get(panda.name, self.defaultCost))
         for panda in turtle.pandas if panda.name not in targets]

class RankingTigress(Tigress):
    """
    Get the ranking results and measure the performance
    Fields:
        
    """
    def retrieve_target(self, entity):
        return entity.get_raw('_relevance', 0)
            
    def supervise(self, turtle, entity):
        t = self.retrieve_target(entity)
        cost = self.costs.get(t, self.defaultCost)
        ys = turtle.mapping[t]
        [panda.add_data(entity, y, cost) for panda, y in izip(turtle.pandas, ys)]
            
    def measure(self, entity, predicted):
        cm = self.confusionMatrix
        target = self.retrieve_target(entity)
        if target not in cm:
            cm[target] = {predicted:1}
        elif predicted not in cm[target]:
            cm[target][predicted] = 1
        else:
            cm[target][predicted] += 1
        self.total += 1
    
    def RMS(self):
        d = 0
        total = 0
        for t in self.confusionMatrix:
            for p in self.confusionMatrix[t]:
                d += self.confusionMatrix[t][p] * abs(t - p)
                total += self.confusionMatrix[t][p]
        return d / total

class SelfTigress(Tigress):
    pass
class SPNTigress(Tigress):
    pass        
class LexiconTigress(Tigress):
    pass        
class CoTigress(Tigress):
    pass

base.register(Tigress)
base.register(PatternTigress)
base.register(MultiLabelTigress)
base.register(SelfTigress)
base.register(SPNTigress)
base.register(LexiconTigress)
base.register(CoTigress)
