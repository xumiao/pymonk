# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
from pymonk.core.monk import *
from pymonk.math.svm_solver_dual import SVMDual

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
        except:
            pass
    
    def solver(self, partition_id):
        if partition_id not in self.solver:
            w = self.panda.getModel(partition_id)
            self.solver[partition_id] = SVMDual(w, self.eps, self.Cp, self.Cn,\
                                                self.lam, self.max_num_iters,\
                                                self.max_num_instances)
        return self.solver[partition_id]