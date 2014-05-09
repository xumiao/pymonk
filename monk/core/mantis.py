# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for 
solving machine learning problems
@author: xm
"""
import base, crane
from ..math.svm_solver_dual import SVMDual
from bson.objectid import ObjectId
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
        if "gamma" not in self.__dict__:
            self.gamma = 1
        if "maxNumIters" not in self.__dict__:
            self.maxNumIters = 1000
        if "maxNumInstances" not in self.__dict__:
            self.maxNumInstances = 1000
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
        crane.mantisStore.update_one_in_fields(self, self.generic())
                
    def get_solver(self, userId):
        try:
            return self.solvers[userId]
        except KeyError:
            logger.info('no solver found for {0}'.format(userId))
            return None

    def train_one(self, userId):
        solver = self.get_solver(userId)
        if solver:
            consensus = self.panda.update_consensus()
            solver.setModel(consensus)
            solver.trainModel(consensus)
    
    def add_data(self, userId, entity, y, c):
        solver = self.get_solver(userId)
        if solver:
            index = solver.setData(entity._features,y,c)
            self.data[userId][entity._id] = (index, y, c)
    
    def aggregate(self, userId):
        # TODO: incremental aggregation
        # TODO: ADMM aggregation
        #logger.debug("self.panda.consensus = {0}".format(self.panda.consensus))     
    
        solver = self.get_solver(userId)            
        consensus = self.panda.consensus
        t = len(self.panda.weights) + 1/self.rho
        if userId in self.panda.weights:
            q = solver.old_q
        else:
            q = consensus
            t += 1
        consensus.add(q, -1.0/t)
        #self.panda.load_one_weight(userId)
        if userId in self.panda.weights:
            q = solver.q
        else:
            q = consensus
        consensus.add(q, 1.0/t)
        self.panda.save_consensus()
    
    def has_user(self, userId):
        return userId in self.data
    
    def has_user_in_store(self, userId):
        field = 'data.{0}'.format(userId)
        return crane.mantisStore.exists_field(self, field)
        
    def add_one(self, userId):
        if not self.has_user_in_store(userId):
            try:
                w = self.panda.get_model(userId)
                self.solvers[userId] = SVMDual(w, self.eps, self.lam,
                                                     self.rho, self.gamma, self.maxNumIters,
                                                     self.maxNumInstances)
                self.data[userId] = {}
                fields = {'data.{0}'.format(userId):{}}
                return crane.mantisStore.update_one_in_fields(self, fields)
            except Exception as e:
                logger.error('can not create a solver for {0}'.format(userId))
                logger.error('error {0}'.format(e.message))
                return False
        else:
            logger.error('mantis {0} already stores user {1}'.format(self._id, userId))
            return False
    
    def remove_one(self, userId):
        if self.has_user_in_store(userId):
            field = 'data.{0}'.format(userId)
            result = crane.mantisStore.remove_field(self, field)
            del self.solvers[userId]
            del self.data[userId]
            return result
        else:
            logger.warning('mantis {0} does not store user {1}'.format(self._id, userId))
            return False            
        
    def load_one(self, userId):
        if self.has_user_in_store(userId):
            fields = ['data.{0}'.format(userId)]
            s = crane.mantisStore.load_one_in_fields(self, fields)
            w = self.panda.get_model(userId)
            solver = SVMDual(w, self.eps, self.lam,
                             self.rho, self.gamma, self.maxNumIters,
                             self.maxNumInstances)
            self.solvers[userId] = solver
    
            #@todo: slow, need to optimize
            da = s['data'][userId]
            da = {ObjectId(k) : v for k,v in da.iteritems()}
            self.data[userId] = da
            ents = crane.entityStore.load_all_by_ids(da.keys())
            for ent in ents:
                index, y, c = da[ent._id]
                ent._features.setIndex(index)
                solver.setData(ent._features, y, c)
            return True
        else:
            logger.warning('mantis {0} does not store user {1}'.format(self._id, userId))
            return False            
    
    def unload_one(self, userId):
        if self.has_user(userId):
            fields = {'data.{0}'.format(userId):{str(k):v for k,v in self.data[userId].iteritems()}}
            result = crane.mantisStore.update_one_in_fields(self, fields)
            del self.solvers[userId]
            del self.data[userId]
            return result
        else:
            logger.warning('mantis {0} does not have user {1}'.format(self._id, userId))
            return False
            
    def save_one(self, userId):
        if self.has_user(userId):
            fields = {'data.{0}'.format(userId):{str(k):v for k,v in self.data[userId].iteritems()}}
            return crane.mantisStore.update_one_in_fields(self, fields)
        else:
            logger.warning('mantis {0} does not have user {1}'.format(self._id, userId))
            return False
            
base.register(Mantis)
