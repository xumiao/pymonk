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
    
    def add_one(self, partition_id):
        pass
    
    def load_one(self, partition_id):
        return True
    
    def save_one(self, partition_id):
        return True
    
    def train_one(self, partition_id):
        pass
    
    def predict(self, partition_id, entity):
        return 0

    def get_model(self, partition_id):
        return None


class ExistPanda(Panda):

    def predict(self, partition_id, entity):
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

    def predict(self, partition_id, entity):
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
        # @error: problematic when saving, only works on updating
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
    
    def has_partition(self, partition_id):
        return partition_id in self.weights
    
    def has_partition_in_store(self, partition_id):
        field = 'weights.{0}'.format(partition_id)
        return crane.pandaStore.exists_field(self, field)
        
    def add_one(self, partition_id):
        if not self.has_partition_in_store(partition_id):
            self.weights[partition_id] = self.consensus.clone()
            field = 'weights.{0}'.format(partition_id)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.weights[partition_id].generic()})
            return result and self.mantis.add_one(partition_id)
        else:
            logger.error('panda {0} already stores partition {1}'.format(self._id, partition_id))
            return False
    
    def remove_one(self, partition_id):
        if self.has_partition_in_store(partition_id):
            field = 'weights.{0}'.format(partition_id)
            result = crane.pandaStore.remove_field(self, field)
            del self.weights[partition_id]
            return result and self.mantis.remove_one(partition_id)
        else:
            logger.error('panda {0} does not store partition {1}'.format(self._id, partition_id))
            return False            
        
    def update_one_weight(self, partition_id):
        field = 'weights.{0}'.format(partition_id)
        pa = crane.pandaStore.load_one_in_fields(self, [field])
        w = self.weights[partition_id]
        if 'weights' in pa:
            w.update(pa['weights'][partition_id])
        else:
            logger.error('can not find partition {0} in panda {1}'.format(partition_id, self._id))
        return w
    
    def update_consensus(self):
        pa = crane.pandaStore.load_one_in_fields(self,['consensus'])
        if 'consensus' in pa:
            self.consensus.update(pa['consensus'])
        return self.consensus
    
    def save_consensus(self):
        crane.pandaStore.update_one_in_fields(self, {'consensus':self.consensus.generic()})
        
    def load_one(self, partition_id):
        if self.has_partition_in_store(partition_id):
            field = 'weights.{0}'.format(partition_id)
            pa = crane.pandaStore.load_one_in_fields(self, [field])
            self.weights[partition_id] = FlexibleVector(generic=pa['weights'][partition_id])
            return self.mantis.load_one(partition_id)
        else:
            logger.error('panda {0} does not store partition {1}'.format(self._id, partition_id))
            return False            

    def unload_one(self, partition_id):
        if self.has_partition(partition_id):
            field = 'weights.{0}'.format(partition_id)
            result = crane.pandaStore.update_one_in_fields(self, {field:self.weights[partition_id].generic()})
            del self.weights[partition_id]
            return result and self.mantis.unload_one(partition_id)
        else:
            logger.error('panda {0} does not have partition {1}'.format(self._id, partition_id))
            return False            
        
    def save_one(self, partition_id):
        if self.has_partition(partition_id):
            field = 'weights.{0}'.format(partition_id)
            crane.pandaStore.update_one_in_fields(self, {field:self.weights[partition_id].generic()})
            return self.mantis.save_one(partition_id)
        else:
            logger.error('panda {0} does not have partition {1}'.format(self._id, partition_id))
            return False            

    def get_model(self, partition_id=None):
        if partition_id is None:
            return self.consensus

        if partition_id in self.weights:
            return self.weights[partition_id]
        else:
            logger.warning('LinearPanda has no model for {0}'.format(partition_id))
            return None
        
    def predict(self, partition_id, entity):
        model = self.get_model(partition_id)
        if model:
            return sigmoid(model.dot(entity._features))
        else:
            return 0

base.register(Panda)
base.register(ExistPanda)
base.register(RegexPanda)
base.register(LinearPanda)
