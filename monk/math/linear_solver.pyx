# -*- coding: utf-8 -*-
"""
Created on Sat Sep 13 13:17:55 2014
Solving a linear problem

@author: Randy
"""

#cython: boundscheck=False
#cython: wraparound=False
from __future__ import division
cimport cython
from libc.stdlib cimport malloc, free, calloc, rand
from monk.math.flexible_vector import FlexibleVector
from monk.utils.utils import encodeMetric
import logging
logger = logging.getLogger('monk.linear_solver')
metricLog = logging.getLogger('metric')

cdef inline _MEM_CHECK(void* p):
    if p == NULL:
        raise MemoryError()

cdef inline int mins(int v1, int v2, int v3):
    if v1 > v2:
        if v2 > v3:
            return v3
        else:
            return v2
    else:
        if v1 > v3:
            return v3
        else:
            return v1
    
cdef inline float max(float v1, float v2):
    if v1 > v2:
        return v1
    else:
        return v2

cdef inline float min(float v1, float v2):
    if v1 > v2:
        return v2
    else:
        return v1

cdef class LinearSolver(object):
    cpdef public float eps
    cpdef public int max_num_iters
    cpdef public int max_num_instances
    cpdef public int num_instances
    cpdef public float rho
    cpdef public float gamma
    cdef public float rho0
    cdef int active_size
    cdef list x # features
    cdef int* y # target array
    cdef int* index # index array
    cdef float* c
    cdef object w
    
    def __init__(self, w, eps, rho, gamma, max_num_iters, max_num_instances):
        # @todo: check x, y, w not None
        # @todo: validate the parameters
        cdef int j
        self.eps = eps
        self.rho = rho
        self.gamma = gamma
        self.w = w
        self.z_mu = FlexibleVector()
        self.dw = FlexibleVector()
        self.max_num_iters = max_num_iters
        self.max_num_instances = max_num_instances
        self.num_instances = 0
        self.rho0 = rho * gamma / (2 * (rho + gamma))
        self.stepSize = 1.0
        
        self.x     = [None for j in xrange(self.max_num_instances)]
        self.y     = <float*>calloc(self.max_num_instances, cython.sizeof(float))
        _MEM_CHECK(self.y)
        self.index = <int*>calloc(self.max_num_instances, cython.sizeof(int))
        _MEM_CHECK(self.index)
        self.c     = <float*>calloc(self.max_num_instances, cython.sizeof(float))
        _MEM_CHECK(self.c)
        for j in xrange(self.max_num_instances):
            self.index[j] = j
            
    def __del__(self):
        if self.y != NULL:
            free(self.y)
        if self.index != NULL:
            free(self.index)
        if self.c != NULL:
            free(self.c)
        del self.dw  
        del self.z_mu

    cdef inline swap(self, int* index, int j, int k):
        cdef int tmp
        tmp = index[j]
        index[j] = index[k]
        index[k] = tmp

    def initialize(self):
        cdef int j
        for j in xrange(self.num_instances):
            self.index[j] = j

    def status(self):
        cdef int j
        cdef float loss
        cdef float l
        loss = 0
        for j in xrange(self.num_instances):
            xj = self.x[j]
            yj = self.y[j]
            cj = self.c[j]
            l = self.w.dot(xj) - yj
            loss += l * l * cj
        return loss
    
    def maxxnorm(self):
        cdef float result
        cdef int j
        result = 0
        for j in xrange(self.num_instances):
            result = max(self.x[j].norm2(), result)
        return result
        
    def setData(self, x, y, c, ind):
        cdef int j = ind
        self.x[j] = x
        self.y[j] = y
        self.c[j] = c
    
    def setModel0(self, z, mu):
        cdef int j
        for j in xrange(self.num_instances):
            self.index[j] = j
        self.w.copyUpdate(z)
        self.w.addFast(mu, -1)
        self.z_mu.copyUpdate(self.w)
        
    def setModel(self, z, mu):
        cdef int j
        self.w.copyUpdate(z)
#        for j in xrange(self.num_instances):
#            self.w.addFast(self.x[j], self.y[j] * self.alpha[j])
        self.w.addFast(mu, -1)
    
    def setGamma(self, gamma):
        self.gamma = gamma
        self.rho0 = self.rho * self.gamma / (2 * (self.rho + self.gamma))
        logger.debug('rho = {0}, gamma = {1}, rho0 = {2}'.format(self.rho, self.gamma, self.rho0))
                
    def setRho(self, rho):        
        self.rho = rho  
        self.rho0 = self.rho * self.gamma / (2 * (self.rho + self.gamma))
        logger.debug('rho = {0}, gamma = {1}, rho0 = {2}'.format(self.rho, self.gamma, self.rho0))
                
    def trainModel(self):
        cdef int j, s, iteration
        cdef float G
        cdef int active_size = self.num_instances
        cdef int* index = self.index
        cdef int yj
        cdef float cj

        logger.debug('rho0 in linear_solver.trainModel {0}'.format(self.rho0))
        logger.debug('num_instances {0}'.format(self.num_instances))
        iteration = 0
        while iteration < self.max_num_iters:

            self.dw.copyUpdate(self.w)
            self.dw.add(self.z_mu, -1.0)
            self.dw.scale(2.0 * self.rho0)
            
            for s in xrange(active_size):
                j  = index[s]
                yj = self.y[j]
                xj = self.x[j]
                cj = self.c[j]
                
                G = (self.w.dot(xj) - yj) * cj * 2.0                
                self.dw.add(xj, G)      # addFast?                                        

            if self.dw.norm <= self.eps:
                break
            else:
               self.w.add(self.dw, -self.stepSize)   
               iteration += 1