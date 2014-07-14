# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
import base, crane
from numpy import sqrt
from ..math.svm_solver_dual import SVMDual
from ..math.flexible_vector import FlexibleVector
from bson.objectid import ObjectId
import logging
logger = logging.getLogger("monk.mantis")

class Mantis(base.MONKObject):
    FEPS   = 'eps'
    FGAMMA = 'gamma'
    FRHO   = 'rho'
    FPANDA = 'panda'
    FDATA  = 'data'
    FDUALS = 'mu'
    FQ     = 'q'
    FDQ    = 'dq'
    FMAX_NUM_ITERS = 'maxNumIters'
    FMAX_NUM_INSTANCES = 'maxNumInstances'
    store = crane.mantisStore
    
    def __default__(self):
        super(Mantis, self).__default__()
        self.eps = 1e-4
        self.gamma = 1
        self.rho = 1
        self.maxNumIters = 1000
        self.maxNumInstances = 1000
        self.panda = None
        self.data = {}
        self.mu = []
        self.q  = []
        self.dq = []
        
    def __restore__(self):
        super(Mantis, self).__restore__()
        self.solver = None
        try:
            self.mu = FlexibleVector(generic=self.mu)
            self.q  = FlexibleVector(generic=self.q)
            self.dq = FlexibleVector(generic=self.dq)
            self.data = {ObjectId(k) : v for k,v in self.data.iteritems()}
            return True
        except Exception as e:
            logger.error('error {0}'.format(e.message))
            logger.error('can not create a solver for {0}'.format(self.panda.name))
            return False
                
    def initialize(self, panda):
        self.panda = panda
        self.solver = SVMDual(self.panda.weights, self.eps, self.rho, self.gamma,
                              self.maxNumIters, self.maxNumInstances)
        ents = crane.entityStore.load_all_by_ids(self.data.keys())
        for ent in ents:
            index, y, c = self.data[ent._id]
            self.solver.setData(ent._features, y, c, index)
        self.solver.num_instances = len(ents)
        keys = self.panda.weights.getKeys()
        self.q.addKeys(keys)
        self.dq.addKeys(keys)
        
    def generic(self):
        result = super(Mantis, self).generic()
        # every mantis should have a panda
        result[self.FPANDA] = self.panda._id
        result[self.FDUALS] = self.mu.generic()
        result[self.FQ]     = self.q.generic()
        result[self.FDQ]    = self.dq.generic()
        result[self.FDATA]  = {str(k) : v for k,v in self.data.iteritems()}
        try:
            del result['solver']
        except Exception as e:
            logger.warning('deleting solver failed {0}'.format(e.message))
        return result

    def clone(self, user, panda):
        obj = super(Mantis, self).clone(user)
        obj.mu = FlexibleVector()
        obj.dq = FlexibleVector()
        obj.q  = self.panda.z.clone()
        obj.panda = panda
        obj.solver = SVMDual(panda.weights, self.eps, self.rho, self.gamma,
                             self.maxNumIters, self.maxNumInstances)
        obj.data = {}
        return obj
    
    def train(self):
        self.solver.setModel(self.q, self.mu)
        self.solver.status()
        self.solver.trainModel()
        self.solver.status()
        self.dq.clear()
        rg = float(self.rho + self.gamma)
        self.dq.add(self.q, - self.gamma / rg)
        self.dq.add(self.panda.weights, self.gamma / rg)
        self.dq.add(self.mu, (self.gamma - self.rho) / rg)
        self.q.add(self.dq, 1)
        logger.debug('relative difference of q {0}'.format(sqrt(self.dq.norm2() / (self.q.norm2() + 1e-12))))
    
    def checkout(self, leader):
        if leader:
            z = crane.pandaStore.load_one({'name':self.panda.name,
                                           'creator':leader},
                                          {'z':True}).get('z',[])
            z = FlexibleVector(generic=z)
            self.mu.copyUpdate(self.q)
            self.mu.add(z, -1)
            del z
        else:
            self.mu.copyUpdate(self.q)
            self.mu.add(self.panda.z, -1)

    def merge(self, follower, m):
        if follower != self.creator:
            fdq = crane.mantisStore.load_one({'name':self.name,
                                              'creator':follower},
                                             {'dq':True}).get('dq',[])
            fdq = FlexibleVector(generic=fdq)
            self.panda.z.add(fdq, 1.0 / (m + 1 / self.rho))
            del fdq
        else:
            self.panda.z.add(self.dq, 1.0 / (m + 1 / self.rho))
            
    def commit(self):
        crane.mantisStore.update_one_in_fields(self, {self.FDUALS : self.mu.generic(),
                                                      self.FQ : self.q.generic(),
                                                      self.FDQ : self.dq.generic()})
    
    def add_data(self, entity, y, c):
        da = self.data
        uuid = entity._id
        if uuid in da:
            ind = da[uuid][0] 
        elif self.solver.num_instances < self.maxNumInstances:
            ind = self.solver.num_instances
            self.solver.num_instances = ind + 1
        else:
            # random replacement policy
            # TODO: should replace the most confident data
            olduuid, (ind, oldy, oldc)  = da.popitem()
        self.solver.setData(entity._features, y, c, ind)
        da[uuid] = (ind, y, c)
        
    def reset(self):
        self.mu.clear()
        self.q.clear()
        self.dq.clear()
        crane.mantisStore.update_one_in_fields(self, {self.FDUALS : [],
                                                      self.FQ : [],
                                                      self.FDQ : []})
        #crane.mantisStore.update_one_in_fields(self, {self.FDATA : {}})
    
base.register(Mantis)
