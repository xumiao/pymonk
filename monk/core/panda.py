# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:53 2013
The basic executor of the machine learning building block, 
i.e., a binary classifier or a linear regressor
@author: xm
"""
from monk.math.flexible_vector import FlexibleVector
from monk.math.cmath import sigmoid
from monk.core.monk import *
import monk.core.mantis as pmantis


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

    def predict(self, partition_id, entity, fields):
        return 0

    def getModel(self, partition_id):
        return None


class ExistPanda(Panda):

    def predict(self, entity, fields=[]):
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

    def generic(self):
        result = super(ExistPanda, self).generic()
        self.appendType(result)


class RegexPanda(Panda):

    def predict(self, partition_id, entity, fields):
        pass

    def generic(self):
        result = super(RegexPanda, self).generic()
        self.appendType(result)


class LinearPanda(MONKObject):

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
            self.mantis = pmantis.Mantis()
        else:
            self.mantis = mantisStore.load_or_create(self.mantis)

        self.mantis.panda = self

    def __defaults__(self):
        super(Panda, self).__defaults__()
        self.weights = {}
        self.consensus = FlexibleVector()
        self.mantis = pmantis.Mantis()

    def generic(self):
        result = super(LinearPanda, self).generic()
        self.appendType(result)
        # @error: problematic when saving
        result['weights'].update([(partition_id, self.weights[partition_id].generic())
                                  for partition_id in self.weights])
        result['consensus'] = self.consensus.generic()
        result['mantis'] = self.mantis._id

    def get_model(self, partition_id):
        if partition_id is None:
            return self.consensus

        if partition_id in self.weights:
            return self.weights[partition_id]

        pandaStore.load_one_in_fields()
        self.weights[partition_id] = FlexibleVector()

    def predict(self, partition_id, entity, fields):
        return sigmoid(self.get_model(partition_id).dot(entity._features))

monkFactory.register(Panda)
monkFactory.register(ExistPanda)
monkFactory.register(RegexPanda)
monkFactory.register(LinearPanda)
