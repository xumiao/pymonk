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
        if partition_id in self.panda.weights:
            w = self.panda.weights[partition_id]
        else:
            w = consensus
            t += 1
        consensus.add(w, -1/t)
        w = self.panda.update_one_weight(partition_id)
        consensus.add(w, 1/t)
        self.panda.save_consensus()
    
    def has_partition(self, partition_id):
        return partition_id in self.data
    
    def has_partition_in_store(self, partition_id):
        field = 'data.{0}'.format(partition_id)
        return crane.mantisStore.exists_field(self, field)
        
    def add_one(self, partition_id):
        if not self.has_partition_in_store(partition_id):
            try:
                w = self.panda.get_model(partition_id)
                self.solvers[partition_id] = SVMDual(w, self.eps, self.lam,
                                                     self.rho, self.maxNumIters,
                                                     self.maxNumInstances)
                self.data[partition_id] = {}
                fields = {'data.{0}'.format(partition_id):{}}
                return crane.mantisStore.update_one_in_fields(self, fields)
            except Exception as e:
                logger.error('can not create a solver for {0}'.format(partition_id))
                logger.error('error {0}'.format(e.message))
                return False
        else:
            logger.error('mantis {0} already stores partition {1}'.format(self._id, partition_id))
            return False
    
    def remove_one(self, partition_id):
        if self.has_partition_in_store(partition_id):
            field = 'data.{0}'.format(partition_id)
            result = crane.mantisStore.remove_field(self, field)
            del self.solvers[partition_id]
            del self.data[partition_id]
            return result
        else:
            logger.warning('mantis {0} does not store partition {1}'.format(self._id, partition_id))
            return False            
        
    def load_one(self, partition_id):
        if self.has_partition_in_store(partition_id):
            fields = ['data.{0}'.format(partition_id)]
            s = crane.mantisStore.load_one_in_fields(self, fields)
            w = self.panda.get_model(partition_id)
            solver = SVMDual(w, self.eps, self.lam,
                             self.rho, self.maxNumIters,
                             self.maxNumInstances)
            self.solvers[partition_id] = solver
    
            #@todo: slow, need to optimize
            da = s['data'][partition_id]
            da = {ObjectId(k) : v for k,v in da.iteritems()}
            self.data[partition_id] = da
            ents = crane.entityStore.load_all_by_ids(da.keys())
            for ent in ents:
                index, y, c = da[ent._id]
                ent._features.setIndex(index)
                solver.setData(ent._features, y, c)
            return True
        else:
            logger.warning('mantis {0} does not store partition {1}'.format(self._id, partition_id))
            return False            
    
    def unload_one(self, partition_id):
        if self.has_partition(partition_id):
            fields = {'data.{0}'.format(partition_id):{str(k):v for k,v in self.data[partition_id].iteritems()}}
            result = crane.mantisStore.update_one_in_fields(self, fields)
            del self.solvers[partition_id]
            del self.data[partition_id]
            return result
        else:
            logger.warning('mantis {0} does not have partition {1}'.format(self._id, partition_id))
            return False
            
    def save_one(self, partition_id):
        if self.has_partition(partition_id):
            fields = {'data.{0}'.format(partition_id):{str(k):v for k,v in self.data[partition_id].iteritems()}}
            return crane.mantisStore.update_one_in_fields(self, fields)
        else:
            logger.warning('mantis {0} does not have partition {1}'.format(self._id, partition_id))
            return False
            
base.register(Mantis)
