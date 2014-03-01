#cython: boundscheck=False
#cython: wraparound=False

from __future__ import division

cimport cython
from libc.stdlib cimport malloc, free, rand, calloc, realloc, RAND_MAX

cdef extern from "math.h":
    float exp(float x)
    
cpdef sigmoid(float v):
    cdef float ev2 = exp(v * 2)
    return 1 - 2 / (ev2 + 1)
