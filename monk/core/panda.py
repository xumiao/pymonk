# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:53 2013
The basic executor of the machine learning building block, 
i.e., a binary classifier or a linear regressor
@author: xm
"""
from ..math.flexible_vector import FlexibleVector
from ..math.cmath import sigmoid
import constants as cons
import base, crane
import re
import logging
logger = logging.getLogger('monk.panda')

class Panda(base.MONKObject):
    FUID  = 'uid'
    FNAME = 'name'
    store = crane.pandaStore
    
    def __default__(self):
        super(Panda, self).__default__()
        self.uid = crane.uidStore.nextUID()
        self.name = 'Var' + str(self.uid)
        
    def has_mantis():
        return False
    
    def add_features(self, uids):
        pass
    
    def train(self):
        pass
    
    def predict(self, entity):
        return 0

class ImmutablePanda(Panda):
    '''
    These pandas won't be replicated for different users
    '''
    def __default__(self):
        super(ImmutablePanda, self).__default__()
        self.creator = cons.DEFAULT_CREATOR
    
    def __restore__(self):
        super(ImmutablePanda, self).__restore__()
        self.creator = cons.DEFAULT_CREATOR
    
    def clone(self, user):
        return self
        
class ExistPanda(ImmutablePanda):

    def predict(self, entity):
        if self.name in entity._raws:
            entity[self.uid] = 1
            return 1
        else:
            return 0

class RegexPanda(ImmutablePanda):

    def __restore__(self):
        super(RegexPanda, self).__restore__()
        self.p = re.compile(self.name)
    
    def generic(self):
        result = super(RegexPanda, self).generic()
        del result['p']
        return result
        
    def predict(self, entity):
        if [v for k,v in entity._raws.iteritems() if self.p.match(k)]:
            entity[self.uid] = 1
            return 1
        else:
            return 0

class LinearPanda(Panda):
    FWEIGHTS = 'weights'
    FMANTIS  = 'mantis'

    def __default__(self):
        super(LinearPanda, self).__default__()
        self.weights = FlexibleVector()
        self.mantis = None

    def __restore__(self):
        super(LinearPanda, self).__restore__()
        self.weights = FlexibleVector(generic=self.weights)
        if isinstance(self.mantis, dict):
            self.mantis['panda'] = self._id
        self.mantis = crane.mantisStore.load_or_create(self.mantis)

    def generic(self):
        result = super(LinearPanda, self).generic()
        result[self.FMANTIS]  = self.mantis.name
        result[self.FWEIGHTS] = self.weights.generic()


        self.weights = {}
        self.local_consensus = {}
        self.dual = {}
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
        del result['local_consensus']           # [TODO]: is it necessary?
        del result['dual']                      # [TODO]: is it necessary?
        return result
    
    def clone(self, user):
        obj = super(LinearPanda, self).clone(user)
        obj.weights = self.weights.clone()
        obj.mantis = self.mantis.clone(user)
        return obj
        
    def save(self, **kwargs):
        super(LinearPanda, self).save(kwargs)
        self.mantis.save(kwargs)
    
    def delete(self):
        result = super(LinearPanda, self).delete()
        result = result & self.mantis.delete()
        return result
        
    def has_mantis(self):
        return True
    
    def add_features(self, uids):
        self.weights.addKeys(uids)
    
    def pull_weights(self):
        genericW = self.store.load_one_in_fields(self, [self.FWEIGHTS])
        self.weights.update(genericW.get(self.FWEIGHTS, []))
    
    def push_weights(self):
        self.store.update_one_in_fields(self, {self.FWEIGHTS:self.weights.generic()})
        
    def predict(self, entity):
        entity[self.uid] = sigmoid(self.weights.dot(entity._features))
        return entity[self.uid]



    def add_one(self, userId):
        if not self.has_user_in_store(userId):
            self.weights[userId] = self.consensus.clone()
            field = 'weights.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.weights[userId].generic()})
            self.local_consensus[userId] = FlexibleVector()
            field = 'local_consensus.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.local_consensus[userId].generic()})
            self.dual[userId] = FlexibleVector()
            field = 'dual.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.dual[userId].generic()})            
            return result and self.mantis.add_one(userId)
        else:
            logger.error('panda {0} already stores user {1}'.format(self._id, userId))
            return False
    
    def remove_one(self, userId):
        if self.has_user_in_store(userId):
            field = 'weights.{0}'.format(userId)
            result = crane.pandaStore.remove_field(self, field)
            del self.weights[userId]
            field = 'local_consensus.{0}'.format(userId)
            result = crane.pandaStore.remove_field(self, field)
            del self.local_consensus[userId]
            field = 'dual.{0}'.format(userId)
            result = crane.pandaStore.remove_field(self, field)
            del self.dual[userId]
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
            
    def load_one_local_consensus(self, userId):
        if self.has_user_in_store(userId):
            field = 'local_consensus.{0}'.format(userId)
            genericW = crane.pandaStore.load_one_in_fields(self, [field])['local_consensus'][userId]
            if userId in self.local_consensus:
                self.local_consensus[userId].update(genericW)
            else:
                self.local_consensus[userId] = FlexibleVector(generic=genericW)
            return True
        else:
            logger.error('panda {0} does not store user {1}'.format(self._id, userId))
            return False 
            
    def load_one_dual(self, userId):
        if self.has_user_in_store(userId):
            field = 'dual.{0}'.format(userId)
            genericW = crane.pandaStore.load_one_in_fields(self, [field])['dual'][userId]
            if userId in self.dual:
                self.dual[userId].update(genericW)
            else:
                self.dual[userId] = FlexibleVector(generic=genericW)
            return True
        else:
            logger.error('panda {0} does not store user {1}'.format(self._id, userId))
            return False         
    
    def load_consensus(self):
        pa = crane.pandaStore.load_one_in_fields(self,['consensus'])
        if 'consensus' in pa:
            self.consensus.update(pa['consensus'])
        return self.consensus
    
    def save_consensus(self):
        crane.pandaStore.update_one_in_fields(self, {'consensus':self.consensus.generic()})

    def save_dual(self, userId):
        field = 'dual.{0}'.format(userId)
        crane.pandaStore.update_one_in_fields(self, {field:self.dual[userId].generic()})      
        
    def load_one(self, userId):
        self.load_one_weight(userId)
        self.mantis.load_one(userId)

    def unload_one(self, userId):
        if self.has_user(userId):
            field = 'weights.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.weights[userId].generic()})
            del self.weights[userId]
            field = 'local_consensus.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.local_consensus[userId].generic()})
            del self.local_consensus[userId]
            field = 'dual.{0}'.format(userId)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.dual[userId].generic()})
            del self.dual[userId]
            return result and self.mantis.unload_one(userId)
        else:
            logger.error('panda {0} does not have user {1}'.format(self._id, userId))
            return False            
        
    def save_one(self, userId):
        if self.has_user(userId):
            field = 'weights.{0}'.format(userId)
            crane.pandaStore.update_one_in_fields(self, {field:self.weights[userId].generic()})
            field = 'local_consensus.{0}'.format(userId)
            crane.pandaStore.update_one_in_fields(self, {field:self.local_consensus[userId].generic()})
            field = 'dual.{0}'.format(userId)
            crane.pandaStore.update_one_in_fields(self, {field:self.dual[userId].generic()})
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
            
    def get_local_consensus(self, userId):
        if userId in self.local_consensus:
            return self.local_consensus[userId]
        else:
            logger.warning('LinearPanda has no local_consensus for {0}'.format(userId))
            return None
            
    def get_dual(self, userId):
        if userId in self.dual:
            return self.dual[userId]
        else:
            logger.warning('LinearPanda has no dual for {0}'.format(userId))
            return None            
        

base.register(Panda)
base.register(ExistPanda)
base.register(RegexPanda)
base.register(LinearPanda)
