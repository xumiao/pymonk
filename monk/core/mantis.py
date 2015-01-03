# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
import base, crane
from constants import EPS
from monk.math.svm_solver_dual import SVMDual
from monk.math.flexible_vector import FlexibleVector
from bson.objectid import ObjectId
from monk.utils.utils import metricValue, metricAbs, metricRelAbs
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

    def clone(self, userName, panda):
        obj = super(Mantis, self).clone(userName)
        obj.mu = FlexibleVector()
        obj.dq = FlexibleVector()
        obj.q  = self.panda.z.clone()
        obj.panda = panda
        obj.solver = SVMDual(panda.weights, self.eps, self.rho, self.gamma,
                             self.maxNumIters, self.maxNumInstances)
        obj.data = {}
        return obj
    
    def train(self, leader):
        if not self.data:
            logger.debug('no data, skip training')
            return
            
        logger.debug('gamma in mantis {0}'.format(self.gamma))

        # check out z
        if leader:
            z = crane.pandaStore.load_one({'name':self.panda.name,
                                           'creator':leader},
                                          {'z':True}).get('z',[])
            z = FlexibleVector(generic=z)
        else:
            z = self.panda.z
        
        if z is None:
            logger.debug('no consensus checked out')
            return
            
        #metricAbs(metricLog, self, '|z|', z)
        #metricAbs(metricLog, self, '|q|', self.q)
        metricRelAbs(self, 'z~q', self.q, z)
        
        # update mu
        self.dq.clear()
        self.dq.add(self.mu, -1)
        self.mu.add(self.q, 1)
        self.mu.add(z, -1)
        self.dq.add(self.mu, 1)
        metricAbs(self, 'mu', self.mu)
        #metricAbs(metricLog, self, '|dmu|', self.dq)
        #metricValue(metricLog, self, 'sup(mu)', 2 * self.solver.num_instances * self.solver.maxxnorm() * z.norm())
        
        # update w
        self.solver.setModel0(z, self.mu)
        #loss = self.solver.status()
        #metricValue(metricLog, self, 'loss', loss)
        #metricRelAbs(metricLog, self, '|q~w|', self.q, self.panda.weights)
        #logger.debug('q = {0}'.format(self.q))
        #logger.debug('w = {0}'.format(self.panda.weights))
        self.solver.trainModel()
        loss = self.solver.status()
        metricValue(self, 'loss', loss)
        metricValue(self, 'x', self.solver.maxxnorm())
        
        # update q
        r = self.rho / float(self.rho + self.gamma)
        self.dq.add(self.q, -1)
        self.q.clear()
        self.q.add(z, r)
        self.q.add(self.panda.weights, 1 - r)
        self.q.add(self.mu, -r)
        self.dq.add(self.q, 1)
        
        if z is not self.panda.z:
            del z
            
        logger.debug('q = {0}'.format(self.q))
        logger.debug('w = {0}'.format(self.panda.weights))
        
        # measure convergence
        #metricAbs(self, '|dq|', self.dq)
        #metricAbs(self, '|q|', self.q)
        metricRelAbs(self, 'q~w', self.q, self.panda.weights)

        # commit changes
        self.panda.update_fields({self.panda.FWEIGHTS:self.panda.weights.generic()})
        self.commit()
    
    def checkout(self, leader):
        pass

    def merge(self, follower, m):
        if follower != self.creator:
            fdq = crane.mantisStore.load_one({'name':self.name,
                                              'creator':follower},
                                             {'dq':True}).get('dq',[])
            fdq = FlexibleVector(generic=fdq)
        else:
            fdq = self.dq

        rd = (fdq.norm() + EPS) / (self.panda.z.norm() + EPS)
        if rd < self.eps:
            logger.debug('Converged, no need to merge')
            return False
        else:
            self.panda.z.add(fdq, 1.0 / (m + 1 / self.rho))
            logger.debug('m = {0}'.format(m))
            logger.debug('update z {0}'.format(self.panda.z))
            logger.debug('relative difference of z {0}'.format(rd))
            metricValue(self, 'rz', rd)
            #self.panda.update_fields({self.panda.FCONSENSUS:self.panda.z.generic()})
        
        if fdq is not self.dq:
            del fdq
        return True
        
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
