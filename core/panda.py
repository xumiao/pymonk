# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:53 2013
The basic executor of the machine learning building block, 
i.e., a binary classifier or a linear regressor
@author: xm
"""
from pymonk.math.flexible_vector import FlexibleVector
from pymonk.math.cmath import sigmoid
from pymonk.core.monk import *
import pymonk.core.mantis as pmantis

class Panda(MONKObject):
    def __restore__(self):
        super(Panda, self).__restore__()
        if "uid" not in self.__dict__:
            self.uid = uidStore.nextUID()
        if "name" not in self.__dict__:
            raise Exception('No name specified')
    
    def __defaults__(self):
        super(Panda, self).__defaults__()
        self.uid = uidStore.nextUID()
        self.name = "Var" + str(self.uid)
    
    def generic(self):
        result = super(Panda, self).generic()
        self.appendType(result)
    
    def predict(self, entity, fields):
        return 0

class ExistPanda(Panda):
    def predict(self, entity, fields = []):
        def extract(x, y):
            try:
                if entity[y].find(self.name) >= 0:
                    return x + 1
                else:
                    return x
            except:
                return x
        if fields:
            return reduce(extract, fields, 0)
        else:
            return reduce(extract, entity.iterkeys(), 0)

class RegexPanda(Panda):
    def predict(self, entity, fields):
        pass
    
class LinearPanda(MONKObject):
    def __restore__(self):
        super(Panda, self).__restore__()
        if "weights" not in self.__dict__:
            self.weights = FlexibleVector()
        else:
            self.weights = FlexibleVector(generic = self.weights)
        if "mantis" not in self.__dict__:
            self.mantis = pmantis.Mantis()
        else:
            try:
                if "panda" not in self.mantis:
                    self.mantis["panda"] = self._id
            except:
                pass
            self.mantis = monkFactory.load_or_create(MantisStore, self.mantis)
        
    def __defaults__(self):
        super(Panda, self).__defaults__()
        self.weights = FlexibleVector()
        self.mantis = pmantis.Mantis()

    def generic(self):
        result = super(Panda, self).generic()
        self.appendType(result)
        result['weights'] = self.weights.generic()
        result['mantis'] = self.mantis._id
    
    def predict(self, entity, fields):
        return sigmoid(self.weights.dot(entity._features))

monkFactory.register("Panda", Panda.create)
monkFactory.register("ExistPanda", ExistPanda.create)
monkFactory.register("RegexPanda", RegexPanda.create)
monkFactory.register("LinearPanda", LinearPanda.create)