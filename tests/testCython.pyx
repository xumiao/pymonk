# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 13:36:14 2013

@author: xm
"""

from __future__ import division

cimport cython
from libc.stdlib cimport malloc, free, rand, calloc, realloc

def testPointer():
    cdef float* w
    
    w = <float*>malloc(10*cython.sizeof(float))
    
    w[0] = 1
    w[1] = 2
    w[2] = 4
    w[3] = 8
    w[4] = 0
    
    cdef float* ww = w
    cdef float result = 0
    
    while ww[0] != 0:
        result += ww[0]
        ww += 1
    
    print result 
    
    free(w)
    
def testPrecision():
    cdef long long index1 = 10
    cdef long long index2 = 20
    cdef long delta = index1 - index2
    print delta
    
def testRealloc():
    cdef float* w = <float*>calloc(10, cython.sizeof(float))
    w[1] = 5
    w = <float*>realloc(w, 14*cython.sizeof(float))
    cdef int i
    for i in xrange(14):
        print w[i]
    free(w)