#cython: boundscheck=False
#cython: wraparound=False

from __future__ import division

cimport cython
from libc.stdlib cimport malloc, free, rand, calloc, realloc, RAND_MAX

cdef extern from "math.h":
    double exp(double x)
    
cpdef sigmoid(double v):
    cdef double ev2 = exp(v * 2)
    return 1 - 2 / (ev2 + 1)
