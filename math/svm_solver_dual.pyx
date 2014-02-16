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
from libc.stdlib cimport malloc, free, calloc
from pymonk.math.flexible_vector import FlexibleVector

cdef inline _MEM_CHECK(void* p):
    if p == NULL:
        raise MemoryError()

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
    
ctypedef FlexibleVecotr* FlexibleVector_t

cdef class SVMDual(object):
    cpdef public float eps
    cpdef public float Cp
    cpdef public float Cn
    cpdef public float pos_neg_ratio
    cpdef public float lam
    cpdef public int max_iter
    cpdef public int max_num_instances
    cpdef public int num_instances
    cpdef public float rho
    cdef int active_size
    cdef FlexibleVector* w # weights
    cdef FlexibleVector** x # features
    cdef int*  y # target array
    cdef int* index # index array
    cdef float* QD
    cdef float* alpha
    cdef float max_score
    cdef int max_score_index
    
    def __init__(self, x, y, w, eps, Cp, Cn, lam, rho, max_iter, max_L):
        cdef int j
        cdef float pos = 1e-8
        cdef float neg = 1e-8
        self.max_L = max_L
        self.index = <int*>malloc(self.max_L * cython.sizeof(int))
        _MEM_CHECK(self.index)
        self.y     = <int*>malloc(self.max_L * cython.sizeof(int))
        _MEM_CHECK(self.y)
        self.x     = <FlexibleVector**>malloc(self.max_L * cython.sizeof(FlexibleVector_t))
        _MEM_CHECK(self.x)
        self.QD    = <float*>malloc(self.max_L * cython.sizeof(float))
        _MEM_CHECK(self.QD)
        self.alpha = <float*>malloc(self.max_L * cython.sizeof(float))
        _MEM_CHECK(self.alpha)
        self.w     = w

        for j in xrange(self.max_L):
            self.index[j] = j
            
        self.active_size = min(len(x), max_L)
        for j in xrange(self.active_size):
            self.y[j] = y[j]
            self.x[j] = x[j]
            if (self.y[j] > 0):
                pos += 1
            else:
                neg += 1
        self.pos_neg_ratio = pos / neg
        self.eps = eps
        self.Cp = Cp
        self.Cn = Cn
        self.lam = lam
        self.max_iter = max_iter
        self.rho = rho

    def __del__(self):
        if self.x != NULL:
            free(self.x)
        if self.y != NULL:
            free(self.y)
        if self.index != NULL:
            free(self.index)
        if self.QD != NULL:
            free(self.QD)
        if self.alpha != NULL:
            free(self.alpha)
    
    cpdef initialization(self):
        cdef int j
        for j in xrange(self.active_size):
            self.alpha[j] = 0
            self.index[j] = j
            if self.y[j] > 0:
                self.QD[j] = 0.5 * self.rho / self.Cp
            else:
                self.QD[j] = 0.5 * self.rho / self.Cn
            self.QD[j] += self.x[j].norm2()
    
    cdef inline swap(self, int* index, int j, int k):
        cdef int tmp
        tmp = index[j]
        index[j] = index[k]
        index[k] = tmp
    
    cpdef status(self, int i):
        cdef float objective = 0
        cdef int j, k
        cdef float* w = self.w[i]
        cdef float** x = self.x[i]
        cdef int* y = self.y[i]
        cdef float* xj
        cdef float g, objective1
        
        for k in xrange(self.nf):
            objective += (w[k] - self.z[k]) * (w[k] - self.z[k])
        objective1 = objective
        objective *= 0.5 * self.rho
        
        for j in xrange(self.L[i]):
            xj = x[j]
            g = 0
            for k in xrange(self.nf):
                g += w[k] * xj[k]
            g = 1 - y[j] * g
            if g > 0:
                if y[j] > 0:
                    objective += self.Cp * g * g
                else:
                    objective += self.Cn * g * g
        print '{0:09.4f} {1:09.4f} {2}'.format(objective1, objective, self.userList[i])
        
    cpdef addData(self, x, y):
        if self.active_size < self.max_L:
            
        pass
        
    cpdef modifyLabel(self, int index, int y):
        self.y[index] = y
        #modify alpha and w to reflect the change
        pass
    
    cpdef updateWeight(self, FlexibleVector* z):
        cdef int j
        cdef float ya
        cdef float* w = self.w
        w.copy(z)
        for j in xrange(self.active_size):
            w.add(self.x[j], self.y[j] * self.alpha[j])
        
    cpdef train(self):
        cdef int j, k, s, iteration
        cdef float ya, d, G, alpha_old
        cdef int active_size = self.active_size
        cdef int* index = self.index
        cdef float* w = self.w
        cdef float* alpha = self.alpha
        cdef float* QD = self.QD
        cdef int yj
        cdef FlexibleVector* xj
    
        # PG: projected gradient, for shrinking and stopping
        cdef float PG
        cdef float PGmax_old = 1e10
        cdef float PGmin_old = -1e10
        cdef float PGmax_new
        cdef float PGmin_new
                 
        iteration = 0
        while iteration < self.max_iter:
            PGmax_new = -1e10
            PGmin_new = 1e10
            
            for j in xrange(active_size):
                k = j + int(np.random.rand() * (active_size - j))
                self.swap(index, j, k)

            for s in xrange(active_size):
                j  = index[s]
                yj = self.y[j]
                xj = self.x[j]
                
                G = w.dot(xj) * yj - 1
                
                if yj > 0:
                    G += alpha[j] * 0.5 * self.rho / self.Cp
                else:
                    G += alpha[j] * 0.5 * self.rho / self.Cn
                
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
                    w.add(xj, d)
                        
            iteration += 1
#            if iteration % 10 == 0:
#                print '.',

            if PGmax_new - PGmin_new <= self.eps:
                if active_size == l:
                    break
                else:
                    active_size = l
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
    