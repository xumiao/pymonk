# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
import base, crane
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
    FSIZE  = 'm'
    FMAX_NUM_ITERS = 'maxNumIters'
    FMAX_NUM_INSTANCES = 'maxNumInstances'
    store = crane.mantisStore
    
    def __default__(self):
        self.eps = 1e-4
        self.gamma = 1
        self.rho = 1
        self.m = 0
        self.maxNumIters = 1000
        self.maxNumInstances = 1000
        self.panda = None
        self.data = {}
        self.mu = FlexibleVector()
        self.q = FlexibleVector()
        self.dq = FlexibleVector()
        
    def __restore__(self):
        super(Mantis, self).__restore__()
        self.solver = None
        try:
            self.solver = SVMDual(self.panda.weights, self.eps, self.gamma * self.rho / (self.gamma + self.rho),
                                  self.maxNumIters, self.maxNumInstances)
            #@todo: slow, need to optimize
            self.data = {ObjectId(k) : v for k,v in self.data.iteritems()}
            ents = crane.entityStore.load_all_by_ids(self.data.keys())
            for ent in ents:
                index, y, c = self.data[ent._id]
                self.solver.setData(ent._features, y, c, index)
            return True
        except Exception as e:
            logger.error('can not create a solver for {0}'.format(self.panda.name))
            logger.error('error {0}'.format(e.message))
            return False

    def generic(self):
        result = super(Mantis, self).generic()
        # every mantis should have a panda
        result[self.FPANDA] = self.panda._id
        result[self.FDUALS] = self.mu.generic()
        result[self.FQ] = self.q.generic()
        result[self.FDQ] = self.dq.generic()
        try:
            del result['solver']
        except Exception as e:
            logger.warning('deleting solver failed {0}'.format(e.message))
        return result

    def clone(self, user, panda):
        obj = super(Mantis, self).clone(user)
        obj.mu = FlexibleVector()
        obj.dq = FlexibleVector()
        obj.q = self.panda.z.clone()
        obj.panda = panda
        obj.solver = SVMDual(panda.weights, self.eps, self.gamma * self.rho / (self.gamma + self.rho),
                             self.maxNumIters, self.maxNumInstances)
        obj.data = {}
        self.m += 1
        return obj
    
    def train(self):
        self.solver.setModel(self.q, self.mu)
        self.solver.trainModel()
        self.dq.clear()
        rg = self.rho + self.gamma
        self.dq.add(self.q, - self.gamma / rg)
        self.dq.add(self.solver.w, self.gamma / rg)
        self.dq.add(self.mu, (self.gamma - self.rho) / rg)
        self.q.add(self.dq)
    
    def checkout(self, leader):
        z = crane.pandaStore.load_one({'name':self.panda.name,
                                       'creator':leader},
                                      {'z':True}).get('z',[])
        z = FlexibleVector(generic=z)
        self.mu.clear()
        self.mu.add(self.q, 1)
        self.mu.add(z, -1)
        del z

    def merge(self, follower):
        fdq = crane.mantisStore.load_one({'name':self.name,
                                          'creator':follower},
                                         {'dq':True}).get('dq',[])
        fdq = FlexibleVector(generic=fdq)
        self.panda.z.add(fdq, 1.0 / (self.m + 1 / self.rho))
        del fdq
        
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
    

base.register(Mantis)
