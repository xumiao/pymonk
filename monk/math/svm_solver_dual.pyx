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
    cdef int active_size
    cdef list x # features
    cdef int* y # target array
    cdef int* index # index array
    cdef float* QD
    cdef float* alpha
    cdef float* c
    cdef float highest_score
    cdef object w
    
    def __init__(self, w, eps, lam, rho, max_num_iters, max_num_instances):
        # @todo: check x, y, w not None
        # @todo: validate the parameters
        cdef int j
        self.eps = eps
        self.lam = lam
        self.rho = rho
        self.w = w
        self.max_num_iters = max_num_iters
        self.max_num_instances = max_num_instances
        self.num_instances = 0
        
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

    def initialization(self):
        cdef int j
        for j in xrange(self.num_instances):
            self.alpha[j] = 0
            self.index[j] = j
            self.QD[j] = 0.5 * self.rho / self.c[j] + self.x[j].norm2()
    
    def setData(self, x, y, c):
        cdef int j
        j = x.getIndex()
        if j >= 0 and j < self.max_num_instances:
            # x is set, use its index, and modify label
            if y == self.y[j]:
                return j
            # TODO: rewind the alpha and weight to remove the old data
            # for now, assume it is just forgotten
        elif self.num_instances < self.max_num_instances:
            # add the data to the end of the arrays
            j = self.num_instances
            self.num_instances += 1
            x.setIndex(j)
        else:
            # pick the last one in the index
            # it is possibly the one far away from the decision boundary
            j = self.index[self.max_num_instances - 1]
            x.setIndex(j)
            
        self.x[j] = x
        self.y[j] = y
        self.c[j] = c
        self.alpha[j] = 0
        self.QD[j] = 0.5 * self.rho / c + x.norm2()
        return x.getIndex()
        
    def setModel(self, z):
        cdef int j
        cdef float ya
        self.w.copyUpdate(z)
        for j in xrange(self.num_instances):
            self.w.addFast(self.x[j], self.y[j] * self.alpha[j])
        
    def trainModel(self):
        cdef int j, k, s, iteration
        cdef float ya, d, G, alpha_old
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
                G += alpha[j] * 0.5 * self.rho / self.c[j]
                
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
#            if iteration % 10 == 0:
#                print '.',

            if PGmax_new - PGmin_new <= self.eps:
                if active_size == self.num_instances:
                    break
                else:
                    active_size = self.num_instances
#                    self.status(i)
                    PGmax_old = 1e10
                    PGmin_old = -1e10
                    continue
                
            PGmax_old = PGmax_new
            PGmin_old = PGmin_new
            if PGmax_old <= 0:
                PGmax_old = 1e10
            if PGmin_old >= 0:
                PGmin_old = -1e10
    