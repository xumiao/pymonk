# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
from base import MONKObject, monkFactory, __DEFAULT_NONE
from base import viperStore, tigressStore
import viper as pviper
import tigress as ptigress
import logging
logger = logging.getLogger("monk")

class Turtle(MONKObject):

    def __restore__(self):
        super(Turtle, self).__restore__()
        if 'viper' in self.__dict__:
            self.viper = viperStore.load_or_create(self.viper)
        else:
            self.viper = pviper.Viper()
        if 'tigress' in self.__dict__:
            self.tigress = tigressStore.load_or_create(self.tigress)
        else:
            self.tigress = ptigress.Tigress()
        if 'name' not in self.__dict__:
            self.name = __DEFAULT_NONE
        if 'description' not in self.__dict__:
            self.description = __DEFAULT_NONE
        if 'pPenalty' not in self.__dict__:
            self.pPenalty = 1.0
        if 'pEPS' not in self.__dict__:
            self.pEPS = 1e-8
        if 'pMaxPathLength' not in self.__dict__:
            self.pMaxPathLength = 1
        if 'pMaxInferenceSteps' not in self.__dict__:
            self.pMaxInferenceSteps = 1

    def __defaults__(self):
        super(Turtle, self).__defaults__()
        self.viper = pviper.Viper()
        self.tigress = ptigress.Tigress()
        self.name = __DEFAULT_NONE
        self.description = __DEFAULT_NONE
        self.pPenalty = 1.0
        self.pEPS = 1e-8
        self.pMaxPathLength = 1
        self.pMaxInferenceSteps = 1

    def generic(self):
        result = super(Turtle, self).generic()
        self.appendType(result)
        result['viper'] = self.viper._id
        result['monkey'] = self.monkey._id
        result['tigress'] = self.tigress._id
        return result

    def add_panda(self, panda):
        pass

    def delete_panda(self, panda):
        pass

    def infer(self, entity):
        pass
#        for panda in self.pandas:
#            entity[panda.Uid] = sigmoid(panda.score(entity))

    def add_data(self, partition_id, entity):
        self.tigress.supervise(self.viper, entity)
        
    def train_one(self, partition_id):
        pass
    
    def save_one(self, partition_id):
        pass

monkFactory.register(Turtle)
