# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
import base, crane
from numpy import sqrt
from monk.math.svm_solver_dual import SVMDual
from monk.math.flexible_vector import FlexibleVector
from bson.objectid import ObjectId
from monk.utils.utils import encodeMetric
import logging

logger = logging.getLogger("monk.mantis")
metricLog = logging.getLogger("metric")

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
    
    def train(self, leader):
        # check out z
        z = self.checkout(leader)
        
        # check if updates are needed
        self.dq.copyUpdate(self.q)
        self.dq.add(z, -1)
        z_q = sqrt(self.dq.norm2()) / (self.q.norm2() + 1e-12)
        logger.debug('|z|={0}'.format(z.norm2()))
        logger.debug('|q|={0}'.format(self.q.norm2()))
        logger.debug('difference between z and q {0}'.format(z_q))
        metricLog.info(encodeMetric(self, '|z-q|/|q|', z_q))
        if z_q < 0.001 and self.q.norm2() > 0:
            logger.debug('no need to train')
            return
            
        # update mu
        self.mu.add(self.q, 1)
        self.mu.add(z, -1)
        logger.debug('gamma in mantis {0}'.format(self.gamma))
        # update w
        self.solver.setModel(z, self.mu)
        loss = self.solver.status()
        logger.debug('objective = {0}'.format(loss))
        metricLog.info(encodeMetric(self, 'loss', loss))
        self.solver.trainModel()
        loss = self.solver.status()
        logger.debug('objective = {0}'.format(loss))
        metricLog.info(encodeMetric(self, 'loss', loss))
        
        # update q
        r = self.rho / float(self.rho + self.gamma)
        self.dq.copyUpdate(self.q)    
        self.q.clear()
        self.q.add(z, r)
        self.q.add(self.panda.weights, 1 - r)
        self.q.add(self.mu, -r)
        self.dq.add(self.q, -1)
        del z
        
        # measure convergence
        rd = sqrt(self.dq.norm2() / (self.q.norm2() + 1e-12))
        logger.debug('relative difference of q {0}'.format(rd))
        metricLog.info(encodeMetric(self, '|dq|/|q|', rd))
        
        # commit changes  
        self.panda.update_fields({self.panda.FWEIGHTS:self.panda.weights.generic()})                            
        self.commit()
    
    def checkout(self, leader):
        if leader:
            z = crane.pandaStore.load_one({'name':self.panda.name,
                                           'creator':leader},
                                          {'z':True}).get('z',[])
            z = FlexibleVector(generic=z)
            return z
        else:
            return self.panda.z

    def merge(self, follower, m):
        if follower != self.creator:
            fdq = crane.mantisStore.load_one({'name':self.name,
                                              'creator':follower},
                                             {'dq':True}).get('dq',[])
            fdq = FlexibleVector(generic=fdq)
        else:
            fdq = self.dq

        rd = sqrt(fdq.norm2() / (self.panda.z.norm2() + 1e-12))
        if rd < 0.001 and self.panda.z.norm2() > 0:
            logger.debug('no need to merge')
        else:
            self.panda.z.add(fdq, - 1.0 / (m + 1 / self.rho))
            logger.debug('m = {0}'.format(m))
            logger.debug('update z {0}'.format(self.panda.z))
            logger.debug('relative difference of z {0}'.format(rd))
            metricLog.info(encodeMetric(self, '|dz|/|z|', rd))
            self.panda.update_fields({self.panda.FCONSENSUS:self.panda.z.generic()})
        
        if fdq is not self.dq:
            del fdq
            
    def commit(self):
        self.update_fields({self.FDUALS : self.mu.generic(),
                            self.FQ     : self.q.generic(),
                            self.FDQ    : self.dq.generic()})        
    
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
        logger.debug('mu {0}'.format(self.mu))
        logger.debug('q  {0}'.format(self.q))
        logger.debug('dq {0}'.format(self.dq))
        self.commit()
        self.solver.initialize()
        
    def reset_data(self):
        self.data = {}
        self.solver.num_instances = 0
        logger.debug('data {0}'.format(self.data))
        self.update_fields({self.FDATA : {}})
        
    def set_mantis_parameter(self, para, value):
        if (para == 'gamma'):
            self.gamma = value
            self.solver.setGamma(value)
            logger.debug('gamma is {0}'.format(self.gamma))
            logger.debug('gamma of solver is {0}'.format(self.solver.gamma))
            self.update_fields({self.FGAMMA : self.gamma})
    
base.register(Mantis)
