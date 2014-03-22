# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:53 2013
The basic executor of the machine learning building block, 
i.e., a binary classifier or a linear regressor
@author: xm
"""
from ..math.flexible_vector import FlexibleVector
from ..math.cmath import sigmoid
import base
from crane import uidStore, mantisStore
from mantis import Mantis
import logging
logger = logging.getLogger('monk.panda')

class Panda(base.MONKObject):

    def __restore__(self):
        super(Panda, self).__restore__()
        if "uid" not in self.__dict__:
            self.uid = uidStore.nextUID()
        if "name" not in self.__dict__:
            logger.error('Panda : no name is specified')
            raise Exception('No name specified')

    def __defaults__(self):
        super(Panda, self).__defaults__()
        self.uid = uidStore.nextUID()
        self.name = "Var" + str(self.uid)
    
    def has_mantis():
        return False
    
    def load(self, partition_id):
        pass
    
    def save(self, partition_id):
        pass
    
    def predict(self, partition_id):
        return 0

    def getModel(self, partition_id):
        return None


class ExistPanda(Panda):

    def predict(self, entity):
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
        super(Panda, self).__restore__()
        if "weights" not in self.__dict__:
            self.weights = {}
        else:
            for partition_id in self.weights:
                self.weights[partition_id] = FlexibleVector(
                    generic=self.weights[partition_id])
        
        if "consensus" not in self.__dict__:
            self.consensus = FlexibleVector()
        else:
            self.consensus = FlexibleVector(generic=self.consensus)

        if "mantis" not in self.__dict__:
            self.mantis = Mantis()
        else:
            self.mantis = mantisStore.load_or_create(self.mantis)

        self.mantis.panda = self

    def __defaults__(self):
        super(Panda, self).__defaults__()
        self.weights = {}
        self.consensus = FlexibleVector()
        self.mantis = Mantis()

    def generic(self):
        result = super(LinearPanda, self).generic()
        # @error: problematic when saving
        result['weights'].update([(partition_id, self.weights[partition_id].generic())
                                  for partition_id in self.weights])
        result['consensus'] = self.consensus.generic()
        result['mantis'] = self.mantis._id
        return result
        
    def get_model(self, partition_id):
        if partition_id is None:
            return self.consensus

        if partition_id in self.weights:
            return self.weights[partition_id]
        else:
            logger.warning('LinearPanda has no model for {0}'.format(partition_id))
            return None
        
    def score(self, partition_id, entity):
        model = self.get_model(partition_id)
        if model:
            return sigmoid(model.dot(entity._features))
        else:
            return 0

base.register(Panda)
base.register(ExistPanda)
base.register(RegexPanda)
base.register(LinearPanda)
