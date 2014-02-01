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
        self.pandas  = loadOrCreateAll(pandaStore,  self.pandas)
        self.monkeys = loadOrCreateAll(monkeyStore, self.monkeys)
        self.mantes  = loadOrCreateAll(mantisStore, self.mantes)
        self.tigers  = loadOrCreateAll(tigerStore,  self.tigers)
    
    def __defaults__(self):
        super(Turtle, self).__defaults__()
        self.pandas  = []
        self.monkeys = []
        self.tigers  = []
        self.mantes  = []
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
        result['pandas']  = GetIds(self.pandas)
        result['monkeys'] = GetIds(self.monkeys)
        result['mantes']  = GetIds(self.mantes)
        result['tigers']  = GetIds(self.tigers)
        return result
    
    def addPanda(self, panda):
        self.pandas.append(panda)
    
    def deletePanda(self, panda):
        self.pandas = filter(lambda x: x._id != panda._id, self.pandas)
    
    def infer(self, entity, fields = {}):
        for panda in self.pandas:
            entity[panda.Uid] = sigmoid(panda.score(entity))
    
    
monkObjectFactory.register("Turtle", Turtle.create)
