# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
import base, crane
from ..math.svm_solver_dual import SVMDual
import logging
logger = logging.getLogger("monk.mantis")

class Mantis(base.MONKObject):

    def __restore__(self):
        super(Mantis, self).__restore__()
        if "eps" not in self.__dict__:
            self.eps = 1e-4
        if "lam" not in self.__dict__:
            self.lam = 1
        if "rho" not in self.__dict__:
            self.rho = 1
        if "max_num_iters" not in self.__dict__:
            self.max_num_iters = 1000
        if "max_num_instances" not in self.__dict__:
            self.max_num_instances = 1000
        if "max_num_partitions" not in self.__dict__:
            self.max_num_partitions = 100
        if "panda" not in self.__dict__:
            self.panda = None
        if "data" not in self.__dict__:
            self.data = {}
        self.solvers = {}

    def generic(self):
        result = super(Mantis, self).generic()
        # every mantis should have a panda
        result['panda'] = self.panda._id
        try:
            del result['solvers']
        except Exception as e:
            logger.warning('deleting solvers failed {0}'.format(e.message))
        return result

    def save(self, **kwargs):
        if kwargs and kwargs.has_key('partition_id'):
            pid = kwargs['partition_id']
            self.save_one(pid)
        else:
            crane.mantisStore.update_one_in_fields(self, self.generic())
                
    def get_solver(self, partition_id):
        try:
            return self.solvers[partition_id]
        except KeyError:
            logger.info('no solver found for {0}'.format(partition_id))
            return None

    def train_one(self, partition_id):
        solver = self.get_solver(partition_id)
        if solver:
            consensus = self.panda.update_consensus()
            solver.setModel(consensus)
            solver.trainModel()
    
    def add_data(self, partition_id, entity, y, c):
        solver = self.get_solver(partition_id)
        if solver:
            index = solver.setData(entity._features,y,c)
            self.data[partition_id][entity._id] = (index, y, c)
    
    def aggregate(self, partition_id):
        # @todo: incremental aggregation
        # @todo: ADMM aggregation
        consensus = self.panda.consensus
        t = len(self.panda.weights)
        if self.panda.weights.has_key(partition_id):
            w = self.panda.weights[partition_id]
        else:
            w = consensus
            t += 1
        consensus.add(w, -1/t)
        w = self.panda.update_one_weight(partition_id)
        consensus.add(w, 1/t)
        self.panda.save_consensus()
        
    def add_one(self, partition_id):
        w = self.panda.get_model(partition_id)
        self.solvers[partition_id] = SVMDual(w, self.eps, self.lam,
                                             self.rho, self.max_num_iters,
                                             self.max_num_instances)
        self.data[partition_id] = {}
    
    def load_one(self, partition_id):
        if self.solvers.has_key(partition_id):
            logger.warning('solver for {0} already exists'.format(partition_id))
            return
        
        fields = ['data.{0}'.format(partition_id)]
        s = crane.mantisStore.load_one_in_fields(self, fields)
        if not s.has_key('data'):
            logger.error('can not load solver for {0}'.format(partition_id))
            return
        
        w = self.panda.get_model(partition_id)
        solver = SVMDual(w, self.eps, self.lam,
                         self.rho, self.max_num_iters,
                         self.max_num_instances)
        self.solvers[partition_id] = solver
        #@todo: slow, need to optimize
        da = self.data[partition_id]
        ents = crane.entityStore.load_all_by_ids(da.keys())
        for ent in ents:
            index, y, c = da[ent._id]
            ent._features.setIndex(index)
            solver.setData(ent._features, y, c)
            
    def save_one(self, partition_id):
        if self.solvers.has_key(partition_id):
            crane.mantisStore.update_one_in_fields(self, {'solvers.{0}'.format(partition_id):self.solvers[partition_id].generic()})
        else:
            logger.warning('can not find solver for {0} to save'.format(partition_id))
            
base.register(Mantis)
