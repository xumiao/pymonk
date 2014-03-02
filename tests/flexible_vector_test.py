# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 21:02:22 2013

@author: xm
"""

import pyximport
pyximport.install(setup_args={"include_dirs": '.'}, reload_support=True)

from timeit import timeit
from core.sparse_vector import SparseVector
from numpy.random import rand


def randomSV(num, th=0.5):
    a = SparseVector()
    for i in range(num):
        if rand() > th:
            a[i] = 1
    return a


def sequentialSV(num):
    a = SparseVector()
    for i in range(num):
        a[i] = i
    return a


def testRandomAdd():
    print timeit("randomSV(10000)",
                 setup="from core.sparse_vector import SparseVector; from tests.sparse_vector_test import randomSV; from numpy.random import rand",
                 number=10)


def testSequentialAdd():
    print timeit("sequentialSV(10000)",
                 setup="from core.sparse_vector import SparseVector; from tests.sparse_vector_test import sequentialSV",
                 number=10)


def testTrim():
    a = SparseVector()
    a[1] = 1
    a[2] = 2
    a[3] = 1e-6
    a[4] = -1e-6
    a[5] = 4
    a[6] = 1e-8
    print a
    a.trim()
    print 'after trim'
    print a
    a.trim(remove=True)
    print 'after remove trim'
    print a


def testInsertRemove():
    a = SparseVector()
    a[1] = 1
    print 'insert 1'
    print a
    a[5] = 5
    print 'insert 5'
    print a
    a[2] = 2
    print 'insert 2'
    print a
    a[10] = 10
    print 'insert 10'
    print a
    a[4] = 4
    print 'insert 4'
    print a
    a[3] = 3
    print 'insert 3'
    print a
    del a[1]
    print 'delete 1'
    print a
    del a[5]
    print 'delete 5'
    print a
    del a[3]
    print 'delete 3'
    print a
    del a[4]
    print 'delete 4'
    print a
