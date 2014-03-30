# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
import base
import constants
import crane
from ..math.cmath import sigmoid, sign0
import tigress as ti
#from itertools import izip
import logging
logger = logging.getLogger("monk.turtle")

class Turtle(base.MONKObject):

    def __restore__(self):
        super(Turtle, self).__restore__()
        if 'pandas' in self.__dict__:
            self.pandas = crane.pandaStore.load_or_create_all(self.pandas)
        else:
            self.pandas = []
        #self.ids = {p._id : i for i, p in izip(range(len(self.pandas)), self.pandas)}
        if 'tigress' in self.__dict__:
            self.tigress = crane.tigressStore.load_or_create(self.tigress)
        else:
            self.tigress = ti.Tigress()
        if "mapping" not in self.__dict__:
            self.mapping = {}
        self.inverted_mapping = {v: k for k, v in self.mapping.iteritems()}
        if 'name' not in self.__dict__:
            self.name = constants.DEFAULT_NONE
        if 'description' not in self.__dict__:
            self.description = constants.DEFAULT_NONE
        if 'pPenalty' not in self.__dict__:
            self.pPenalty = 1.0
        if 'pEPS' not in self.__dict__:
            self.pEPS = 1e-8
        if 'pMaxPathLength' not in self.__dict__:
            self.pMaxPathLength = 1
        if 'pMaxInferenceSteps' not in self.__dict__:
            self.pMaxInferenceSteps = 1
        if "maxNumPartitions" not in self.__dict__:
            self.maxNumPartitions = 100
        if "requires" not in self.__dict__:
            logger.info('turtle {0} will use all features seen'.format(self.name))
        elif 'uids' in self.requires:
            uids = self.requires['uids']
            if isinstance(uids, basestring):
                uids = eval(uids)
            [panda.add_features(uids) for panda in self.pandas]
        elif 'turtle_ids' in self.requires:
            turtles = crane.turtleStore.load_all_by_ids(self.requires['turtle_ids'])
            [panda.add_features(turtle.get_panda_uids()) for turtle in turtles for panda in self.pandas]
        else:
            logger.error('dependent features are either in uids or turtle_ids, but not in {0}'.format(self.require))
            

    def generic(self):
        result = super(Turtle, self).generic()
        result['tigress'] = self.tigress._id
        result['pandas'] = [panda._id for panda in self.pandas]
        # inverted_mapping is created from mapping
        del result['inverted_mapping']
        #del result['ids']
        return result
    
    def save(self, **kwargs):
        crane.turtleStore.update_one_in_fields(self, self.generic())
        self.tigress.save()
        [pa.save() for pa in self.pandas]

    def get_panda_uids(self):
        return [pa.uid for pa in self.pandas]
        
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
        return predicted

    def add_data(self, partition_id, entity):
        return self.tigress.supervise(self, partition_id, entity)
        
    def train_one(self, partition_id):
        [panda.mantis.train_one(partition_id) for panda in self.pandas if panda.has_mantis()]
        [panda.save_one(partition_id) for panda in self.pandas]
    
    def aggregate(self, partition_id):
        [panda.mantis.aggregate(partition_id) for panda in self.pandas if panda.has_mantis()]
    
    def has_partition(self, partition_id):
        if not self.tigress.has_partition(partition_id) or \
            [False for panda in self.pandas if not panda.has_partition(partition_id)]:
            return False
        return True
    
    def has_partition_in_store(self, partition_id):
        if not self.tigress.has_partition_in_store(partition_id) or \
            [False for panda in self.pandas if not panda.has_partition_in_store(partition_id)]:
            return False
        return True

    def not_has_partition(self, partition_id):
        if self.tigress.has_partition(partition_id) or \
            [True for panda in self.pandas if panda.has_partition(partition_id)]:
            return False
        return True
    
    def not_has_partition_in_store(self, partition_id):
        if self.tigress.has_partition_in_store(partition_id) or \
            [True for panda in self.pandas if panda.has_partition_in_store(partition_id)]:
            return False
        return True
        
    def add_one(self, partition_id):
        if self.tigress.num_partition() >= self.maxNumPartitions:
            logger.warning('maximun number ({0}) of partitions has been reached'.format(self.maxNumPartitions))
            return False
        
        if not self.tigress.add_one(partition_id):
            return False
        
        if [False for panda in self.pandas if not panda.add_one(partition_id)]:
            return False
            
        return True
    
    def remove_one(self, partition_id):
        if not self.tigress.remove_one(partition_id):
            return False
            
        if [False for panda in self.pandas if not panda.remove_one(partition_id)]:
            return False
            
        return True
        
    def load_one(self, partition_id):
        if self.tigress.num_partition() >= self.maxNumPartitions:
            logger.warning('maximun number ({0}) of partitions has been reached'.format(self.maxNumPartitions))
            return False
        
        if not self.tigress.load_one(partition_id):
            return False
            
        if [False for panda in self.pandas if not panda.load_one(partition_id)]:
            return False
            
        return True
    
    def unload_one(self, partition_id):
        if not self.tigress.unload_one(partition_id):
            return False
        
        if [False for panda in self.pandas if not panda.unload_one(partition_id)]:
            return False
        
        return True
        
    def save_one(self, partition_id):
        if not self.tigress.save_one(partition_id):
            return False
            
        if [False for panda in self.pandas if not panda.save_one(partition_id)]:
            return False
        
        return True

class SingleTurtle(Turtle):
    
    def predict(self, partition_id, entity):
        panda = self.pandas[0]
        entity[panda.uid] = sigmoid(panda.predict(partition_id, entity))
        if sign0(entity[panda.Uid]) > 0:
            self.tigress.measure(partition_id, entity, panda.name)
            return panda.name
        else:
            self.tigress.measure(partition_id, entity, constants.DEFAULT_NONE)
            return constants.DEFAULT_NONE
        
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
