# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:40 2013
The binary or linear optimizer that is the basic building block for solving machine learning problems
@author: xm
"""
from pymonk.core.monk import *
from pymonk.math.flexible_vector import FlexibleVector
from pymonk.math.svm_solver_dual import SVMDual

class Mantis(MONKObject):
    def __restore__(self):
        super(Mantis, self).__restore__()
        if "panda" not in self.__dict__:
            raise Exception('No panda specified")
        else:
            self.panda = monkFactory.load_or_create(pandaStore, self.panda)
        if "eps" not in self.__dict__:
            self.eps = 1e-4
        if "Cp" not in self.__dict__:
            self.Cp = 1
        if "Cn" not in self.__dict__:
            self.Cn = 1
        if "lam" not in self.__dict__:
            self.lam = 1
        if "max_iter" not in self.__dict__:
            self.max_iter = 1000
        if "max_L" not in self.__dict__:
            self.max_L = 1000
        if "rho" not in self.__dict__:
            self.rho = 1
        if "max_users" not in self.__dict__:
            self.max_users = 100
        
        self.Cp = 1
        self.Cn = 1
        self.lam = 1
        self.max_iter = 1000
        self.rho = 1
        self.users = {}
        self.userList = []
        self.M = 0
        self.x = []
        self.y = []
        self.QD = []
        self.alpha = []
        self.w = []
        self.z = []
            
        cpdef public float eps
        cpdef public float Cp
        cpdef public float Cn
        cpdef public float lam
        cpdef public int max_iter
        cpdef public float rho
        cpdef public dict users
        cdef public list userList
        cdef int M # M users
        cdef int nf # number of features
        cdef float*** x # features matrix per user
        cdef int**  y # target array per user
        cdef int* L # L instances per user
        cdef int** index # index array per user
        cdef float** QD
        cdef float** alpha
        cdef float** w
        cdef float* z
        cdef float* xmin
        cdef float* xmax
    
    def __defaults__(self):
        super(Mantis, self).__defaults__()
        self.panda = None
        self.eps = 1e-4
        self.Cp = 1
        self.Cn = 1
        self.lam = 1
        self.max_iter = 1000
        self.rho = 1
        self.users = {}
        self.userList = []
        self.M = 0
        self.x = []
        self.y = []
        self.QD = []
        self.alpha = []
        self.w = []
        self.z = []
        self.xmin = []
        self.xmax = []
        
    def generic(self):
        result = super(Mantis, self).generic()
        self.appendType(result)
        
    