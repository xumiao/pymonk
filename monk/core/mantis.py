# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
from base import MONKObject, monkFactory, pandaStore
from ..math.svm_solver_dual import SVMDual
from ..math.flexible_vector import FlexibleVector
import logging
logger = logging.getLogger("monk")

class Mantis(MONKObject):

    def __restore__(self):
        super(Mantis, self).__restore__()
        if "eps" not in self.__dict__:
            self.eps = 1e-4
        if "Cp" not in self.__dict__:
            self.Cp = 1
        if "Cn" not in self.__dict__:
            self.Cn = 1
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
        self.solvers = {}
        self.panda = None

    def __defaults__(self):
        super(Mantis, self).__defaults__()
        self.panda = None
        self.eps = 1e-4
        self.Cp = 1
        self.Cn = 1
        self.lam = 1
        self.rho = 1
        self.max_num_iters = 1000
        self.max_num_instances = 1000
        self.max_num_partitions = 100
        self.solvers = {}

    def generic(self):
        result = super(Mantis, self).generic()
        self.appendType(result)
        # every mantis should have a panda
        result['panda'] = self.panda._id
        # @todo: store the solvers locally or somewhere for faster initialization
        try:
            del result['solvers']
        except Exception as e:
            logger.warning('deleting solvers failed {0}'.format(e.message))

    def get_solver(self, partition_id):
        try:
            return self.solvers[partition_id]
        except KeyError:
            if partition_id is None:
                logger.warning('trying to get None solver')
                return None
            else:
                logger.info('adding a solver for {0}'.format(partition_id))
                w = self.panda.getModel(partition_id)
                solver = SVMDual(w, self.eps, self.lam, self.Cp, self.Cn,
                                 self.rho, self.max_num_iters,
                                 self.max_num_instances)
                self.solvers[partition_id] = solver
                return solver

    def train_one(self, partition_id):
        solver = self.get_solver(partition_id)
        if solver:
            solver.trainModel()
    
    def set_data(self, partition_id, x, y, c):
        solver = self.get_solver(partition_id)
        if solver:
            solver.setData(x,y)
    
    def aggregate(self):
        # @todo: incremental aggregation
        # @todo: ADMM aggregation
        consensus = FlexibleVector()
        t = 1 / len(self.weights)
        [consensus.add(w, t) for w in self.weights.values]
        self.panda.consensus = consensus
        
    def save_model(self, partition_id):
        w = self.panda.getModel(partition_id)
        if partition_id is None:
            field = 'consensus'
        else:
            field = 'weights.{0}'.format(partition_id)
        pandaStore.update_one(self.panda, {field : w.generic()})

monkFactory.register(Mantis)
