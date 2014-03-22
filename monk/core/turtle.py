# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
import base
from crane import tigressStore, pandaStore
from ..math.cmath import sigmoid, sign0
from tigress import Tigress
from itertools import izip
import logging
logger = logging.getLogger("monk.turtle")

class Turtle(base.MONKObject):

    def __restore__(self):
        super(Turtle, self).__restore__()
        if 'pandas' in self.__dict__:
            self.pandas = pandaStore.load_or_create_all(self.pandas)
        else:
            self.pandas = []
        #self.ids = {p._id : i for i, p in izip(range(len(self.pandas)), self.pandas)}
        if 'tigress' in self.__dict__:
            self.tigress = tigressStore.load_or_create(self.tigress)
        else:
            self.tigress = Tigress()
        if "mapping" not in self.__dict__:
            self.mapping = {}
        self.inverted_mapping = {v: k for k, v in self.mapping.iteritems()}
        if 'name' not in self.__dict__:
            self.name = base.__DEFAULT_NONE
        if 'description' not in self.__dict__:
            self.description = base.__DEFAULT_NONE
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
        self.tigress = Tigress()
        self.pandas = []
        #self.ids = {}
        self.mapping = {}
        self.inverted_mapping = {}
        self.name = base.__DEFAULT_NONE
        self.description = base.__DEFAULT_NONE
        self.pPenalty = 1.0
        self.pEPS = 1e-8
        self.pMaxPathLength = 1
        self.pMaxInferenceSteps = 1

    def generic(self):
        result = super(Turtle, self).generic()
        result['tigress'] = self.tigress._id
        result['pandas'] = [panda._id for panda in self.pandas]
        # inverted_mapping is created from mapping
        del result['inverted_mapping']
        #del result['ids']
        return result

    def add_panda(self, panda):
        pass
    
    def delete_panda(self, panda):
        pass
            
    def predict(self, partition_id, entity):
        def _predict(panda):
            entity[panda.Uid] = sigmoid(panda.predict(partition_id, entity))
            return sign0(entity[panda.Uid])
        predicted = self.inverted_mapping[tuple([_predict(panda) for panda in self.pandas])]
        self.tigress.measure(partition_id, entity, predicted)

    def add_data(self, partition_id, entity):
        self.tigress.supervise(self, partition_id, entity)
        
    def train_one(self, partition_id):
        [panda.mantis.train_one(partition_id) for panda in self.pandas if panda.has_mantis()]
    
    def load_one(self, partition_id):
        if not self.tigress.has_partition(partition_id):
            self.tigress.load(partition_id)
            [panda.load(partition_id) for panda in self.pandas]
    
    def save_one(self, partition_id):
        if self.tigress.has_partition(partition_id):
            self.tigress.save(partition_id)
            [panda.save(partition_id) for panda in self.pandas]

class SingleTurtle(Turtle):
    
    def predict(self, partition_id, entity):
        panda = self.pandas[0]
        entity[panda.Uid] = sigmoid(panda.predict(partition_id, entity))
        if sign0(entity[panda.Uid]) > 0:
            self.tigress.measure(partition_id, entity, panda.name)
            return panda.name
        else:
            self.tigress.measure(partition_id, entity, base.__DEFAULT_NONE)
            return base.__DEFAULT_NONE
        
    def train_one(self, partition_id):
        panda = self.pandas[0]
        if panda.has_mantis():
            panda.mantis.train_one(partition_id)
    
class RankingTurtle(Turtle):
        
    def predict(self, partition_id, entity):
        pass
    
    def add_data(self, partition_id, entity):
        pass
    
    def train_one(self, partition_id):
        pass
    
    def load_one(self, partition_id):
        pass
    
    def save_one(self, partition_id):
        pass
    
class SPNTurtle(Turtle):
    pass
    
base.register(Turtle)
base.register(SingleTurtle)
base.register(RankingTurtle)
base.register(SPNTurtle)
