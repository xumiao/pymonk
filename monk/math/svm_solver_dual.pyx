# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 18:43:29 2014
Solving a linear svm in dual

@todo: memory pool
@todo: online normalization
@author: pacif_000
"""
#cython: boundscheck=False
#cython: wraparound=False
from __future__ import division
cimport cython
from libc.stdlib cimport malloc, free, calloc, rand
from monk.math.flexible_vector import FlexibleVector
import logging
logger = logging.getLogger('monk.svm_solver_dual')

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

cdef class SVMDual(object):
    cpdef public float eps
    cpdef public float lam
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
    cdef float* QD
    cdef float* alpha
    cdef float* c
    cdef float highest_score
    cdef object w
    
    def __init__(self, w, eps, rho, gamma, max_num_iters, max_num_instances):
        # @todo: check x, y, w not None
        # @todo: validate the parameters
        cdef int j
        self.eps = eps
        self.rho = rho
        self.gamma = gamma
        self.w = w
        self.max_num_iters = max_num_iters
        self.max_num_instances = max_num_instances
        self.num_instances = 0
        self.rho0 = rho * gamma / (2 * (rho + gamma))
        
        self.x     = [None for j in xrange(self.max_num_instances)]
        self.y     = <int*>calloc(self.max_num_instances, cython.sizeof(int))
        _MEM_CHECK(self.y)
        self.index = <int*>calloc(self.max_num_instances, cython.sizeof(int))
        _MEM_CHECK(self.index)
        self.QD    = <float*>calloc(self.max_num_instances, cython.sizeof(float))
        _MEM_CHECK(self.QD)
        self.alpha = <float*>calloc(self.max_num_instances, cython.sizeof(float))
        _MEM_CHECK(self.alpha)
        self.c     = <float*>calloc(self.max_num_instances, cython.sizeof(float))
        _MEM_CHECK(self.c)
        for j in xrange(self.max_num_instances):
            self.index[j] = j
            
    def __del__(self):
        if self.y != NULL:
            free(self.y)
        if self.index != NULL:
            free(self.index)
        if self.QD != NULL:
            free(self.QD)
        if self.alpha != NULL:
            free(self.alpha)
        if self.c != NULL:
            free(self.c)

    cdef inline swap(self, int* index, int j, int k):
        cdef int tmp
        tmp = index[j]
        index[j] = index[k]
        index[k] = tmp

    def initialize(self):
        cdef int j
        for j in xrange(self.num_instances):
            self.alpha[j] = 0
            self.index[j] = j
            self.QD[j] = self.rho0 / self.c[j] + self.x[j].norm2()

    def status(self):
        cdef int j
        cdef float loss
        cdef float l
        loss = 0
        for j in xrange(self.num_instances):
            xj = self.x[j]
            yj = self.y[j]
            l = max(0, 1 - self.w.dot(xj) * yj) 
            loss += l * l
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
        self.alpha[j] = 0
        self.QD[j] = self.rho0 / c + x.norm2()
    
    def setModel0(self, z, mu):
        cdef int j
        for j in xrange(self.num_instances):
            self.alpha[j] = 0
            self.index[j] = j
        self.w.copyUpdate(z)
        self.w.addFast(mu, -1)
        
    def setModel(self, z, mu):
        cdef int j
        self.w.copyUpdate(z)
        for j in xrange(self.num_instances):
            self.w.addFast(self.x[j], self.y[j] * self.alpha[j])
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
        cdef int j, k, s, iteration
        cdef float d, G, alpha_old
        cdef int active_size = self.num_instances
        cdef int* index = self.index
        cdef float* alpha = self.alpha
        cdef float* QD = self.QD
        cdef int yj
    
        # PG: projected gradient, for shrinking and stopping
        cdef float PG
        cdef float PGmax_old = 1e10
        cdef float PGmin_old = -1e10
        cdef float PGmax_new
        cdef float PGmin_new
        logger.debug('rho0 in svm_solver_dual.trainModel {0}'.format(self.rho0))
        logger.debug('num_instances {0}'.format(self.num_instances))
        iteration = 0
        while iteration < self.max_num_iters:
            PGmax_new = -1e10
            PGmin_new = 1e10
            for j in xrange(active_size):
                k = j + rand() % (active_size - j)
                self.swap(index, j, k)

            for s in xrange(active_size):
                j  = index[s]
                yj = self.y[j]
                xj = self.x[j]
                
                G = self.w.dot(xj) * yj - 1
                G += alpha[j] * self.rho0 / self.c[j]
                
                PG = 0
                if alpha[j] <= 0:
                    if G > PGmax_old:
                        active_size -= 1
                        self.swap(index, s, active_size)
                        s -= 1
                        continue
                    elif G < 0:
                        PG = G
                else:
                    PG = G
                
                PGmax_new = max(PGmax_new, PG)
                PGmin_new = min(PGmin_new, PG)
                
                if PG > 1e-12 or PG < -1e-12:
                    alpha_old = alpha[j]
                    alpha[j] = max(alpha[j] - G / QD[j], 0)
                    d = (alpha[j] - alpha_old) * yj
                    self.w.addFast(xj, d)
                        
            iteration += 1

            if PGmax_new - PGmin_new <= self.eps:
                if active_size == self.num_instances:
                    break
                else:
                    active_size = self.num_instances
                    PGmax_old = 1e10
                    PGmin_old = -1e10
                    continue
                
            PGmax_old = PGmax_new
            PGmin_old = PGmin_new
            if PGmax_old <= 0:
                PGmax_old = 1e10
            if PGmin_old >= 0:
                PGmin_old = -1e10
