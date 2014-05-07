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
        if "displayTextFields" not in self.__dict__:
            self.displayTextFields = []
        if "displayImageFields" not in self.__dict__:
            self.displayImageField = None
        if "activeBatchSize" not in self.__dict__:
            self.activeBatchSize = 10
        if "defaultCost" not in self.__dict__:
            if len(self.costs) > 0:
                self.defaultCost = min(self.costs.values())
            else:
                self.defaultCost = 1.0
    
    def generic(self):
        result = super(Tigress, self).generic()
        try:
            del result['confusionMatrix']
        except Exception as e:
            logger.warning('deleting solvers failed {0}'.format(e.message))
        return result
    
    def save(self, **kwargs):
        crane.tigressStore.update_one_in_fields(self, self.generic())
    
    def num_user(self):
        return len(self.confusionMatrix)
        
    def has_user(self, userId):
        return userId in self.confusionMatrix
    
    def has_user_in_store(self, userId):
        field = 'confusionMatrix.{0}'.format(userId)
        return crane.tigressStore.exists_field(self, field)
        
    def measure(self, userId, entity, predicted):
        cm = self.confusionMatrix[userId]
        for target in self.retrieve_target(entity):
            if target not in cm:
                cm[target] = {predicted:1}
            elif predicted not in cm[target]:
                cm[target][predicted] = 1
            else:
                cm[target][predicted] += 1
        if '__total__' not in cm:
            cm['__total__'] = 1
        else:
            cm['__total__'] += 1
    
    def delete(self):
        return crane.tigressStore.delete_by_id(self._id)
        
    def add_one(self, userId):
        if not self.has_user_in_store(userId):
            self.confusionMatrix[userId] = {}
            return self.save_one(userId)
        else:
            logger.error('tigress {0} already stores user {1}'.format(self._id, userId))
            return False
    
    def remove_one(self, userId):
        if self.has_user_in_store(userId):
            if userId in self.confusionMatrix:
                del self.confusionMatrix[userId]
            field = 'confusionMatrix.{0}'.format(userId)
            return crane.tigressStore.remove_field(self, field)
        else:            
            logger.error('tigress {0} does not store user {1}'.format(self._id, userId))
            return False
            
    def load_one(self, userId):
        if self.has_user_in_store(userId):
            field = 'confusionMatrix.{0}'.format(userId)
            tg = crane.tigressStore.load_one_in_fields(self, [field])
            self.confusionMatrix[userId] = tg['confusionMatrix'][userId]
            return True
        else:
            logger.error('tigress {0} does not store user {1}'.format(self._id, userId))
            return False

    def unload_one(self, userId):
        if self.has_user(userId):
            field = 'confusionMatrix.{0}'.format(userId)
            result = crane.tigressStore.update_one_in_fields(self, {field:self.confusionMatrix[userId]})
            del self.confusionMatrix[userId]
            return result
        else:
            logger.warning('tigress {0} does not has user {1}'.format(self._id, userId))
            return False
        
    def save_one(self, userId):
        if self.has_user(userId):
            field = 'confusionMatrix.{0}'.format(userId)
            return crane.tigressStore.update_one_in_fields(self, {field:self.confusionMatrix[userId]})
        else:
            logger.warning('tigress {0} does not has user {1}'.format(self._id, userId))
            return False
            
    def retrieve_target(self, entity):
        return () # an empty iterator
    
    def accuracy(self, userId, target):
        try:
            return self.confusionMatrix[userId][target]
        except:
            logger.warning('target {0} not found in confusion matrix'.format(target))
            return {}
        
    def supervise(self, turtle, userId, entity):
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
        combinedField = ' . '.join([utils.translate(getattr(entity, field, ""), ' . ') for field in self.fields])
        logger.debug('combinedField {0}'.format(combinedField))
        return (t for r, t in self.p.iteritems() if r.search(combinedField))
    
    def _supervise(self, turtle, userId, entity, tags):
        for t in tags:
            cost = self.costs.get(t, self.defaultCost)
            ys = turtle.mapping[t]
            [panda.mantis.add_data(userId, entity, y, cost) for panda, y in izip(turtle.pandas, ys)]
            if self.mutualExclusive:
                return True

        if self.defaulting and not tags:
            # no pattern found, add all negative
            [panda.mantis.add_data(userId, entity, -1, self.defaultCost) for panda in turtle.pandas]
        
    def supervise(self, turtle, userId, entity=None):
        if entity:
            self._supervise(turtle, userId, entity, self.retrieve_target(entity))
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
                            self._supervise(turtle, userId, ent, tags)
                    logger.info('training')
                    turtle.train_one(userId)
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
    def measure(self, userId, entity, predicted):
        cm = self.confusionMatrix[userId]
        target = tuple(self.retrieve_target(entity))
        predicted = tuple(predicted)
        if target not in cm:
            cm[target] = {predicted:1}
        elif predicted not in cm[target]:
            cm[target][predicted] = 1
        else:
            cm[target][predicted] += 1
        if '__total__' not in cm:
            cm['__total__'] = 1
        else:
            cm['__total__'] += 1

    def accuracy(self, userId, target):
        try:
            return self.confusionMatrix[userId][target]
        except:
            logger.warning('target {0} not found in confusion matrix'.format(target))
            return {}

    def _supervise(self, turtle, userId, entity, tags):
        targets = set(tags)
        [panda.mantis.add_data(userId, entity, 1, self.costs.get(panda.name, self.defaultCost))
         for panda in turtle.pandas if panda.name in targets]
        [panda.mantis.add_data(userId, entity, -1, self.costs.get(panda.name, self.defaultCost))
         for panda in turtle.pandas if panda.name not in targets]
    
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
