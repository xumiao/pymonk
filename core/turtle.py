# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
from pymonk.core.monk import *
from pymonk.utils.utils import GetIds
from datetime import datetime
from bson.objectid import ObjectId
from pymonk.math.cmath import sigmoid

class Turtle(MONKObject):
    def __restore__(self):
        super(Turtle, self).__restore__()
        self.viper   = monkFactory.load_or_create(viperStore,  self.viper)
        self.monkey  = monkFactory.load_or_create(monkeyStore, self.monkey)
        self.tigress = monkFactory.load_or_create(tigressStore,  self.tigress)
    
    def __defaults__(self):
        super(Turtle, self).__defaults__()
        self.viper = None
        self.monkey = None
        self.tigress  = None
        self.name = __DEFAULT_NONE
        self.description = __DEFAULT_NONE
        self.creator = __DEFAULT_CREATOR
        self.createdTime = datetime.now()
        self.pPenalty = 1.0
        self.pEPS = 1e-8
        self.pMaxPathLength = 1
        self.pMaxInferenceSteps = 1
        
    def generic(self):
        result = super(Turtle, self).generic()
        self.appendType(result)
        result['lastModified'] = datetime.now()
        result['viper']   = self.viper._id
        result['monkey']  = self.monkey._id
        result['tigress'] = self.tigress._id
        return result
    
    def addPanda(self, panda):
        pass
    
    def deletePanda(self, panda):
        pass
    
    def infer(self, entity, fields = {}):
        pass
#        for panda in self.pandas:
#            entity[panda.Uid] = sigmoid(panda.score(entity))
    
    
monkFactory.register("Turtle", Turtle.create)
