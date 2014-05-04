# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:53 2013
The basic executor of the machine learning building block, 
i.e., a binary classifier or a linear regressor
@author: xm
"""
from ..math.flexible_vector import FlexibleVector
from ..math.cmath import sigmoid
import base, crane
from mantis import Mantis
import logging
logger = logging.getLogger('monk.panda')

class Panda(base.MONKObject):

    def __restore__(self):
        super(Panda, self).__restore__()
        if "uid" not in self.__dict__:
            self.uid = crane.uidStore.nextUID()
        if "name" not in self.__dict__:
            logger.warning('no name is specified, using default')
            self.name = 'Var' + str(self.uid)

    def save(self, **kwargs):
        crane.pandaStore.update_one_in_fields(self, self.generic())
        
    def has_mantis():
        return False
    
    def add_features(self, uids):
        pass
    
    def add_one(self, userId):
        pass
    
    def load_one(self, userId):
        return True
    
    def save_one(self, userId):
        return True
    
    def train_one(self, userId):
        pass
    
    def predict(self, userId, entity):
        return 0

    def get_model(self, userId):
        return None


class ExistPanda(Panda):

    def predict(self, userId, entity):
        def extract(x, y):
            try:
                if entity[y].find(self.name) >= 0:
                    return x + 1
                else:
                    return x
            except:
                return x
        return reduce(extract, entity.iterkeys(), 0)

class RegexPanda(Panda):

    def predict(self, userId, entity):
        pass

class LinearPanda(Panda):

    def __restore__(self):
        super(LinearPanda, self).__restore__()
        self.weights = {}
        if "consensus" not in self.__dict__:
            self.consensus = FlexibleVector()
        else:
            self.consensus = FlexibleVector(generic=self.consensus)

        if "mantis" not in self.__dict__:
            self.mantis = Mantis()
        else:
            self.mantis = crane.mantisStore.load_or_create(self.mantis)

        self.mantis.panda = self

    def generic(self):
        result = super(LinearPanda, self).generic()
        result['consensus'] = self.consensus.generic()
        result['mantis'] = self.mantis._id
        del result['weights']
        return result
    
    def save(self, **kwargs):
        crane.pandaStore.update_one_in_fields(self, self.generic())
        self.mantis.save()
            
    def has_mantis(self):
        return True
    
    def add_features(self, uids):
        self.consensus.addKeys(uids)
    
    def has_user(self, userId):
        return userId in self.weights
    
    def has_user_in_store(self, userId):
        field = 'weights.{0}'.format(userId)
        return crane.pandaStore.exists_field(self, field)
        
    def add_one(self, userId):
        if not self.has_user_in_store(userId):
            self.weights[userId] = self.consensus.clone()
            field = 'weights.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.weights[userId].generic()})
            return result and self.mantis.add_one(userId)
        else:
            logger.error('panda {0} already stores user {1}'.format(self._id, userId))
            return False
    
    def remove_one(self, userId):
        if self.has_user_in_store(userId):
            field = 'weights.{0}'.format(userId)
            result = crane.pandaStore.remove_field(self, field)
            del self.weights[userId]
            return result and self.mantis.remove_one(userId)
        else:
            logger.error('panda {0} does not store user {1}'.format(self._id, userId))
            return False            
        
    def load_one_weight(self, userId):
        if self.has_user_in_store(userId):
            field = 'weights.{0}'.format(userId)
            genericW = crane.pandaStore.load_one_in_fields(self, [field])['weights'][userId]
            if userId in self.weights:
                self.weights[userId].update(genericW)
            else:
                self.weights[userId] = FlexibleVector(generic=genericW)
            return True
        else:
            logger.error('panda {0} does not store user {1}'.format(self._id, userId))
            return False            
    
    def update_consensus(self):
        pa = crane.pandaStore.load_one_in_fields(self,['consensus'])
        if 'consensus' in pa:
            self.consensus.update(pa['consensus'])
        return self.consensus
    
    def save_consensus(self):
        crane.pandaStore.update_one_in_fields(self, {'consensus':self.consensus.generic()})
        
    def load_one(self, userId):
        self.load_one_weight(userId)
        self.mantis.load_one(userId)

    def unload_one(self, userId):
        if self.has_user(userId):
            field = 'weights.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.weights[userId].generic()})
            del self.weights[userId]
            return result and self.mantis.unload_one(userId)
        else:
            logger.error('panda {0} does not have user {1}'.format(self._id, userId))
            return False            
        
    def save_one(self, userId):
        if self.has_user(userId):
            field = 'weights.{0}'.format(userId)
            crane.pandaStore.update_one_in_fields(self, {field:self.weights[userId].generic()})
            return self.mantis.save_one(userId)
        else:
            logger.error('panda {0} does not have user {1}'.format(self._id, userId))
            return False            

    def get_model(self, userId=None):
        if userId is None:
            return self.consensus

        if userId in self.weights:
            return self.weights[userId]
        else:
            logger.warning('LinearPanda has no model for {0}'.format(userId))
            return None
        
    def predict(self, userId, entity):
        model = self.get_model(userId)
        if model:
            return sigmoid(model.dot(entity._features))
        else:
            return 0

base.register(Panda)
base.register(ExistPanda)
base.register(RegexPanda)
base.register(LinearPanda)
