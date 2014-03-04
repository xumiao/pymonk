# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
from monk.core.base import MONKObject, monkFactory, __DEFAULT_NONE
from monk.core.base import viperStore, monkeyStore, tigressStore
import monk.core.viper as pviper
import monk.core.monkey as pmonkey
import monk.core.tigress as ptigress


class Turtle(MONKObject):

    def __restore__(self):
        super(Turtle, self).__restore__()
        if 'viper' in self.__dict__:
            self.viper = viperStore.load_or_create(self.viper)
        else:
            self.viper = pviper.Viper()
        if 'monkey' in self.__dict__:
            self.monkey = monkeyStore.load_or_create(self.monkey)
        else:
            self.monkey = pmonkey.Monkey()
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
        self.monkey = pmonkey.Monkey()
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

    def addPanda(self, panda):
        pass

    def deletePanda(self, panda):
        pass

    def infer(self, entity, fields={}):
        pass
#        for panda in self.pandas:
#            entity[panda.Uid] = sigmoid(panda.score(entity))

    def addData(self, entity, fields={}):
        pass

    def changeLabel(self, entity, fields={}):
        pass


monkFactory.register(Turtle)
