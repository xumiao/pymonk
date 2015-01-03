# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:53 2013
The basic executor of the machine learning building block, 
i.e., a binary classifier or a linear regressor
@author: xm
"""
from monk.math.flexible_vector import FlexibleVector
from monk.math.cmath import sigmoid
from mantis import Mantis
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
    
    def checkout(self):
        pass
    
    def merge(self, follower):
        pass
    
    def commit(self):
        pass
    
    def predict(self, entity):
        return 0
    
    def reset(self):
        pass

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
    
    def clone(self, userName):
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
    FWEIGHTS      = 'weights'
    FMANTIS       = 'mantis'
    FCONSENSUS    = 'z'
    FNUMFOLLOWERS = 'm'

    def __default__(self):
        super(LinearPanda, self).__default__()
        self.weights = []
        self.z       = []
        self.mantis  = None
        self.m       = 1

    def __restore__(self):
        super(LinearPanda, self).__restore__()
        self.weights = FlexibleVector(generic = self.weights)
        self.z       = FlexibleVector(generic = self.z)

    def generic(self):
        result = super(LinearPanda, self).generic()
        if self.mantis_loaded():
            result[self.FMANTIS] = self.mantis.signature()
        result[self.FWEIGHTS]   = self.weights.generic()
        result[self.FCONSENSUS] = self.z.generic()
        return result

    def clone(self, userName):
        obj = super(LinearPanda, self).clone(userName)
        obj.weights = self.weights.clone()
        obj.z       = obj.weights.clone()
        obj.m       = 1
        self.load_mantis()
        obj.mantis = self.mantis.clone(userName, obj)
        return obj
        
    def save(self):
        super(LinearPanda, self).save()
        if self.mantis_loaded():
            self.mantis.save()
    
    def delete(self):
        result = super(LinearPanda, self).delete()
        try:
            result = result & self.mantis.delete()
        except:
            self.load_mantis()
            result = result & self.mantis.delete()
        return result
        
    def has_mantis(self):
        return True
    
    def mantis_loaded(self):
        return isinstance(self.mantis, Mantis)
    
    def load_mantis(self):
        if self.mantis_loaded():
            return
            
        if self.mantis is None:
            self.mantis = {Mantis.MONK_TYPE:'Mantis',
                           Mantis.NAME:self.name}

        try:
            self.mantis.setdefault(Mantis.CREATOR, self.creator)
            self.mantis.setdefault(Mantis.FPANDA, self)
        except:
            logger.error('mantis should be a dict for loading')
            logger.error('now is {0}'.format(self.mantis))
            return
            
        self.mantis = crane.mantisStore.load_or_create(self.mantis, True)
        self.mantis.initialize(self)

    def add_data(self, entity, y, c):
        try:
            self.mantis.add_data(entity, y, c)
        except:
            self.load_mantis()
            self.mantis.add_data(entity, y, c)
    
    def increment(self):
        self.m += 1
        self.update_fields({self.FNUMFOLLOWERS:self.m})
    
    def decrease(self):
        self.m -= 1
        self.update_fields({self.FNUMFOLLOWERS:self.m})
        
    def add_features(self, uids):
        self.weights.addKeys(uids)
        self.z.addKeys(uids)
    
    def pull_model(self):
        genericW = self.store.load_one_in_fields(self, [self.FWEIGHTS, self.FCONSENSUS])
        self.weights.update(genericW.get(self.FWEIGHTS, []))
        self.z.update(genericW.get(self.FCONSENSUS, []))
    
    def push_model(self):
        self.update_fields({self.FWEIGHTS:self.weights.generic(),
                            self.FCONSENSUS:self.z.generic()})
    
    def train(self, leader):
        try:
            self.mantis.train(leader)
        except:
            self.load_mantis()
            self.mantis.train(leader)
    
    def checkout(self, leader):
        try:
            self.mantis.checkout(leader)
        except:
            self.load_mantis()
            self.mantis.checkout(leader)
    
    def commit(self):
        self.push_model()
        try:
            self.mantis.commit()
        except:
            self.load_mantis()
            self.mantis.commit()
    
    def merge(self, follower):
        try:
            return self.mantis.merge(follower, self.m)
        except:
            self.load_mantis()
            return self.mantis.merge(follower, self.m)
    
    def predict(self, entity):
        value = self.weights.dot(entity._features)
        entity[self.uid] = sigmoid(value)
        return entity[self.uid]
    
    def reset(self):
        self.weights.clear()
        self.z.clear()
        logger.debug('weights {0}'.format(self.weights))
        logger.debug('z {0}'.format(self.z))
        self.update_fields({self.FWEIGHTS:[],
                            self.FCONSENSUS:[]})
        logger.debug('resetting mantis')
        try:
            self.mantis.reset()
        except:
            crane.mantisStore.update_in_fields({Mantis.NAME:self.name, Mantis.CREATOR:self.creator}, 
                                               {Mantis.FDUALS : [], Mantis.FQ : [], Mantis.FDQ : []})

    def reset_data(self):        
        logger.debug('resetting data in mantis')
        try:
            self.mantis.reset_data()
        except:
            crane.mantisStore.update_in_fields({Mantis.NAME:self.name, Mantis.CREATOR:self.creator}, 
                                               {Mantis.FDATA : {}})                                               

    def set_mantis_parameter(self, para, value):                                               
        try:
            self.mantis.set_mantis_parameter(para, value)
        except:
            self.load_mantis()
            self.mantis.set_mantis_parameter(para, value)
                                   
base.register(Panda)
base.register(ExistPanda)
base.register(RegexPanda)
base.register(LinearPanda)