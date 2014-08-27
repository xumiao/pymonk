# -*- coding: utf-8 -*-
"""
Created on Sat Oct 12 22:32:16 2013
Highly optimized Sparse Vector implemented based on SkipList
It has the following advantages:
1. Allows dynamic insertion, deletion, and modification. 
   All in O(logn) scale due to SkipList properties.
2. Smoothly transits from sparse vector and dense vector, when the indices are adjacent.
   If the resulting index space contains entire range, e.g., [1,2,3], it behaves like a dense array.
   If the resulting indices are completely seperated, e.g., [1,3,5], it behaves like a SkipList.
   If the resulting indices are partially connected, e.g., [1,2,5], it is a SkipList on top of segments.
3. It speedups the following computation scenarios on vector addition and dot products:
   1). Very sparse data operations. 
   2). Dense data operations.
   3). Very sparse data on Dense data.
4. It saves quite amount of memory on both dense and sparse data
5. It performs moderately worse in mildly sparse data, i.e., sparsity range between 0.3-0.8.
   About 20 times slower than numpy array
   
@author: xm
"""
#cython: boundscheck=False
#cython: wraparound=False

from __future__ import division

cimport cython
from libc.stdlib cimport malloc, free, rand, calloc, realloc, RAND_MAX
from libc.string cimport memset
from libc.math cimport sqrt

cdef int MAX_HEIGHT = 32
cdef long MAX_CAPACITY = 2 << 16

cdef struct SkipNodeA:
    int height
    long long index
    long length
    long capacity
    float* values
    SkipNodeA** nextA

ctypedef SkipNodeA* SkipNodeA_t

ctypedef float (*funcA)(float)

# utitily inline math function
cdef inline float _FABS(float v):
    if v > 0:
        return v
    else:
        return -v

cdef inline long long _MAX(long long a, long long b):
    if a > b:
        return a
    else:
        return b

cdef inline long long _MIN(long long a, long long b):
    if a > b:
        return b
    else:
        return a

cdef inline float _MATCH(float v):
    if v < 0:
        return 1
    else:
        return -1

cdef inline float _SQUARE(float v):
    return v * v

# inline memory functions
cdef inline _MEM_CHECK(void* p):
    if p == NULL:
        raise MemoryError()

cdef inline long long _SIZE_OF(SkipNodeA* sn):
    return cython.sizeof(SkipNodeA) +\
           cython.sizeof(SkipNodeA_t) * sn.height +\
           sn.capacity * cython.sizeof(float)

# SkipNodeA functions
cdef bint _setValue(SkipNodeA* sn, long long index, float value):
    if sn == NULL:
        return False
        
    cdef long relative_index = index - sn.index
    if relative_index >= 0 and relative_index < sn.length:
        sn.values[relative_index] = value
        return True
    elif relative_index == sn.length:
        if sn.length == sn.capacity:
            sn.capacity *= 2
            sn.values = <float*>realloc(sn.values, sn.capacity * cython.sizeof(float))
            _MEM_CHECK(sn.values)
        sn.values[relative_index] = value
        sn.length += 1
        return True
    else:
        return False

cdef float _getValue(SkipNodeA* sn, long long index):
    if sn == NULL:
        return 0
    
    cdef long relative_index = index - sn.index
    if relative_index >= 0 and relative_index < sn.length:
        return sn.values[relative_index]
    else:
        return 0

cdef SkipNodeA** _newSkipNodeS(int num, SkipNodeA* target):
    cdef SkipNodeA** p = <SkipNodeA**>malloc(cython.sizeof(SkipNodeA_t) * num)
    _MEM_CHECK(p)
    cdef int i
    for i in xrange(num):
        p[i] = target
    return p

cdef SkipNodeA* _newSkipNodeV(int height, long long index, long length, float* values):
    #height > 0
    #length > 1
    cdef long i
    cdef SkipNodeA* sn = <SkipNodeA*>malloc(cython.sizeof(SkipNodeA))
    _MEM_CHECK(sn)
    sn.height   = height
    sn.index    = index
    sn.length   = length
    sn.capacity = length
    sn.values = <float*>calloc(sn.capacity, cython.sizeof(float))
    _MEM_CHECK(sn.values)
    for i in xrange(length):
        sn.values[i] = values[i]
    sn.nextA = _newSkipNodeS(height, NULL)
    return sn
    
cdef SkipNodeA* _newSkipNodeA(int height, long long index, float value):
    #height > 0
    cdef SkipNodeA* sn = <SkipNodeA*>malloc(cython.sizeof(SkipNodeA))
    _MEM_CHECK(sn)
    sn.height   = height
    sn.index    = index
    sn.length   = 1
    sn.capacity = 1
    sn.values = <float*>calloc(sn.capacity, cython.sizeof(float))
    _MEM_CHECK(sn.values)
    sn.values[0] = value
    sn.nextA = _newSkipNodeS(height, NULL)
    return sn

cdef SkipNodeA* _copySkipNodeA(SkipNodeA* other, float w):
    cdef long i
    cdef SkipNodeA* sn = <SkipNodeA*>malloc(cython.sizeof(SkipNodeA))
    _MEM_CHECK(sn)
    sn.height = other.height
    sn.index = other.index
    sn.length = other.length
    sn.capacity = other.capacity
    sn.values = <float*>calloc(other.capacity, cython.sizeof(float))
    _MEM_CHECK(sn.values)
    for i in xrange(sn.length):
        sn.values[i] = other.values[i] * w
    sn.nextA = _newSkipNodeS(sn.height, NULL)
    return sn
    
cdef void _delSkipNodeA(SkipNodeA* sn):
    if (sn != NULL):
        if (sn.values != NULL):
            free(sn.values)
        if (sn.nextA != NULL):
            free(sn.nextA)
        free(sn)

cdef void _delSkipList(SkipNodeA* head):
    cdef SkipNodeA* currA = head
    cdef SkipNodeA* nextA = head
    while(currA != NULL):
        nextA = currA.nextA[0]
        _delSkipNodeA(currA)
        currA = nextA

cdef class FlexibleVector(object):
    cdef int __index #used as back index holder
    cdef int height
    cdef float queryLength
    cdef long queries
    cdef SkipNodeA* head
    cdef SkipNodeA** found
    
    def __init__(self, *arguments, **keywords):
        self.__index = -1
        self.queryLength = 1
        self.queries = 1
        self.height = 0
        self.head   = _newSkipNodeA(MAX_HEIGHT, -1, -1)
        self.found  = _newSkipNodeS(MAX_HEIGHT, self.head)
        if "generic" in keywords:
            self.update(keywords["generic"])
        
    def __dealloc__(self):
        _delSkipList(self.head)
        if self.found != NULL:
            free(self.found)
        
    def __setitem__(self, key, value):
        self.upsert(key, value)
    
    def __getitem__(self, key):
        return self.find(key)
    
    def __delitem__(self, key):
        self.remove(key)
    
    def __contains__(self, key):
        return self.find(key) != 0
    
    def __str__(self):
        a = []
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef int height, j
        cdef long i
        cdef int mini, maxi
        cdef float minv, maxv
        cdef float v
        mini = -1
        maxi = -1
        minv =  RAND_MAX
        maxv = -RAND_MAX
        while currA != NULL:
            b = []
            for height in xrange(currA.height):
                b.append('*')
            for height in xrange(currA.height, self.height):
                b.append('|')
            for i in xrange(currA.length):
                v = currA.values[i]
                if v != 0 and i < 4:
                    b.append('{0}:{1:.4}'.format(currA.index + i, v))
                if v > maxv:
                    maxv = v
                    maxi = currA.index + i
                if v < minv:
                    minv = v
                    mini = currA.index + i
            b.append('...')
            a.append(' '.join(b))
            currA = currA.nextA[0]
        if mini >= 0 and maxi >= 0:
            a.append('[{0}:{1},{2}:{3}]'.format(mini, minv, maxi, maxv))
        return '\n'.join(a)
        
    def __repr__(self):
        return str(self)

    def all_str(self):
        a = []
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef int height
        cdef long i
        while currA != NULL:
            b = []
            for height in xrange(currA.height):
                b.append('*')
            for height in xrange(currA.height, self.height):
                b.append('|')
            for i in xrange(currA.length):
                b.append('{0}:{1:.4}'.format(currA.index + i, currA.values[i]))
            a.append(' '.join(b))
            currA = currA.nextA[0]
        return '\n'.join(a)

    cpdef setIndex(self, int index):
        self.__index = index
    
    cpdef getIndex(self):
        return self.__index
        
    def _memorySize(self):
        cdef long long size = _SIZE_OF(self.head) + MAX_HEIGHT * cython.sizeof(SkipNodeA_t)
        cdef SkipNodeA* currA = self.head.nextA[0]
        while currA != NULL:
            size += _SIZE_OF(currA)
            currA = currA.nextA[0]
        return size
    
    def _numOfNodes(self):
        cdef long long size = 0
        cdef SkipNodeA* currA = self.head.nextA[0]
        while currA != NULL:
            size += 1
            currA = currA.nextA[0]
        return size
    
    def _maxHeight(self):
        return self.height

    # for debugging usage    
    def printFound(self):
        for height in xrange(self.height):
            print self.found[height].index
    
    def generic(self):
        cdef list a = []
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        while currA != NULL:
            for i in xrange(currA.length):
                if currA.values[i] != 0:
                    a.append((i + currA.index, currA.values[i]))
            currA = currA.nextA[0]
        return a
    
    cpdef clear(self):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        while currA != NULL:
            for i in xrange(currA.length):
                currA.values[i] = 0
            currA = currA.nextA[0]
        
    cpdef copyUpdate(self, FlexibleVector other):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        while currA != NULL:
            for i in xrange(currA.length):
                currA.values[i] = 0
            currA = currA.nextA[0]
        currA = other.head.nextA[0]
        while currA != NULL:
            for i in xrange(currA.length):
                self.upsert(i + currA.index, currA.values[i])
            currA = currA.nextA[0]
        
    def update(self, list f):
        # bulk-insertion can not handle more than 2^32 entries although indices can exceed 2^32
        cdef long i
        for i in xrange(len(f)):
            self.upsert(f[i][0], f[i][1])
            
    def addKeys(self, list f):
        cdef long sz = len(f)
        cdef long i
        for i in xrange(sz):
            if self.find(f[i]) == 0:
                self.upsert(f[i], 0)
    
    def getKeys(self):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        cdef list keys = []
        while currA != NULL:
            for i in xrange(currA.length):
                keys.append(currA.index + i)
            currA = currA.nextA[0]
        return keys
        
    def queryStats(self):
        print self.queryLength / self.queries
        print self.queryLength / self.queries, self._numOfNodes()
    
    def clone(self):
        cdef FlexibleVector c = FlexibleVector()
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef int height
        cdef long i
        while currA != NULL:
            for i in xrange(currA.length):
                c[currA.index + i] = currA.values[i]
            currA = currA.nextA[0]
        return c
    
    cdef foreach(self, funcA func):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        while currA != NULL:
            for i in xrange(currA.length):
                currA.values[i] = func(currA.values[i])
            currA = currA.nextA[0]

    cdef float forall(self, funcA func):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        cdef float result = 0
        while currA != NULL:
            for i in xrange(currA.length):
                result += func(currA.values[i])
            currA = currA.nextA[0]
        return result
        
    cdef int randomHeight(self):
        cdef int height = 1
        while rand() & 1:
            height += 1
        if height > MAX_HEIGHT:
            height = MAX_HEIGHT
        if height > self.height: 
            self.height = height
        return height

    cdef redueHeight(self):
        cdef int height = self.height - 1
        while self.head.nextA[height] == NULL:
            height -= 1
        self.height = height + 1

    cdef inline updateQueryLength(self, int l):
        self.queries += 1
        self.queryLength += l
        
    cdef bint updateList(self, long long index):
        cdef int height
        cdef SkipNodeA* currA = self.found[0]
        cdef SkipNodeA* nextA = currA.nextA[0]
        cdef int l = 0
        if currA != NULL and nextA != NULL:
            if nextA.index <= index and nextA.index + nextA.length >= index:
                self.updateQueryLength(1)
                return True
            elif index > nextA.index + nextA.length and nextA.nextA[0] != NULL:
                # one lookahead
                currA = nextA
                nextA = currA.nextA[0]
                if nextA.index <= index and nextA.index + nextA.length >= index:
                    self.updateQueryLength(2)
                    for height in xrange(currA.height):
                        self.found[height] = currA
                    return True
                
        
        currA = self.head
        for height in reversed(xrange(self.height)):
            nextA = currA.nextA[height]
            while nextA != NULL and nextA.index + nextA.length < index:
                # allow the array to grow at the end
                currA = currA.nextA[height]
                nextA = currA.nextA[height]
                l += 1
            self.found[height] = currA
        self.updateQueryLength(l)
        return nextA != NULL

    cdef float find(self, long long index):
        cdef SkipNodeA* currA
        cdef long i
        if self.updateList(index):
            currA = self.found[0].nextA[0]
            i = index - currA.index
            if i >= 0 and i < currA.length:
                return currA.values[i]
        return 0

    cdef remove(self, long long index):
        cdef SkipNodeA* currA
        cdef SkipNodeA* split
        cdef long delta, i
        cdef int height
        if self.updateList(index):
            currA = self.found[0].nextA[0]
            if currA.index > index:
                return
            
            if currA.length == 1:
                for height in xrange(currA.height):
                    self.found[height].nextA[height] = currA.nextA[height]
                _delSkipNodeA(currA)
                self.redueHeight()
            else:
                if currA.index == index:
                    currA.index += 1
                    currA.length -= 1
                    for i in xrange(currA.length):
                        currA.values[i] = currA.values[i + 1]
                    currA.values[currA.length] = 0
                elif currA.index + currA.length - 1 == index:
                    currA.length -= 1
                    currA.values[currA.length] = 0
                else:
                    # split the node into two
                    newHeight = self.randomHeight()
                    delta = index + 1 - currA.index
                    split = _newSkipNodeV(newHeight, index + 1, currA.length - delta, currA.values + delta)
                    currA.length = index - currA.index
                    currA.values[currA.length] = 0
                    for height in xrange(newHeight):
                        if self.found[height].nextA[height] != currA:
                            split.nextA[height] = self.found[height].nextA[height]
                            self.found[height].nextA[height] = split
                        else:
                            split.nextA[height] = currA.nextA[height]
                            currA.nextA[height] = split

    cdef bint _upsert(self, long long index, float value):
        cdef int newHeight, height
        cdef long i
        cdef SkipNodeA* candidate

        if self.updateList(index):
            candidate = self.found[0].nextA[0]
            i = index - candidate.index
            if i == candidate.length:
                # insert at the end of the candidate node
                if candidate.length == candidate.capacity:
                    candidate.capacity *= 2
                    candidate.values = <float*>realloc(candidate.values, candidate.capacity * cython.sizeof(float))
                    _MEM_CHECK(candidate.values)
                candidate.values[i] = value
                candidate.length += 1
                return True
            elif i >= 0 and i < candidate.length:
                # update the value
                candidate.values[i] = value
                return False

        # insert a new node
        newHeight = self.randomHeight()
        candidate = _newSkipNodeA(newHeight, index, value)
        for height in xrange(newHeight):
            candidate.nextA[height] = self.found[height].nextA[height]
            self.found[height].nextA[height] = candidate
        return True
        
    cdef upsert(self, long long index, float value):
        cdef int height
        cdef long i, oldLength
        cdef SkipNodeA* candidate
        cdef SkipNodeA* neighbor
        if self._upsert(index, value):
            # merge the neighboring node after insertion
            candidate = self.found[0].nextA[0]
            neighbor  = candidate.nextA[0]
            if neighbor != NULL and candidate.index + candidate.length == neighbor.index:
                # copy neighboring values
                oldLength = candidate.length
                candidate.length += neighbor.length
                if candidate.length > candidate.capacity:
                    candidate.capacity += neighbor.capacity
                    candidate.values = <float*>realloc(candidate.values, candidate.capacity * cython.sizeof(float))
                    _MEM_CHECK(candidate.values)
                for i in xrange(neighbor.length):
                    candidate.values[oldLength + i] = neighbor.values[i]
                # remove the neighboring node
                for height in xrange(neighbor.height):
                    if self.found[height].nextA[height] == candidate:
                        candidate.nextA[height] = neighbor.nextA[height]
                    else:
                        self.found[height].nextA[height] = neighbor.nextA[height]
                _delSkipNodeA(neighbor)
                self.redueHeight()
            
    cpdef scale(self, float w):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        while currA != NULL:
            for i in xrange(currA.length):
                currA.values[i] *= w
            currA = currA.nextA[0]
    
    cpdef float norm1(self):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        cdef float result = 0
        while currA != NULL:
            for i in xrange(currA.length):
                result += _FABS(currA.values[i])
            currA = currA.nextA[0]
        return result   
    
    cpdef float norm2(self):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        cdef float result = 0
        while currA != NULL:
            for i in xrange(currA.length):
                result += currA.values[i] * currA.values[i]
            currA = currA.nextA[0]
        return result
        
    cpdef float norm(self):
        return sqrt(self.norm2())
        
    cpdef trim(self, float tol = 0.00001, bint remove = False):
        cdef SkipNodeA* currA = self.head.nextA[0]
        cdef long i
        while currA != NULL:
            i = currA.length - 1
            while i >= 0:
                if _FABS(currA.values[i]) < tol:
                    if remove:
                        self.remove(currA.index + i)
                    else:
                        currA.values[i] = 0
                i -= 1
            currA = currA.nextA[0]
                
    cpdef float dot(self, FlexibleVector other):
        cdef SkipNodeA* currA1 = self.head.nextA[0]
        cdef SkipNodeA* currA2 = other.head.nextA[0]
        cdef float result = 0.0
        if currA1 == NULL or currA2 == NULL:
            return result
            
        cdef long long frontier = currA2.index
        cdef long long delta = frontier - currA1.index
        cdef long long endIndex1, endIndex2
        cdef float* f1
        cdef float* f2
        while 1:
            endIndex1 = currA1.index + currA1.length
            endIndex2 = currA2.index + currA2.length

            if delta > 0:
                if frontier < endIndex1:
                    delta = 0
                else:
                    delta = frontier - endIndex1
            elif delta < 0:
                if frontier - delta < endIndex2:
                    frontier -= delta
                    delta = 0
                else:
                    delta += endIndex2 - frontier
                    frontier = endIndex2

            f1 = currA1.values + frontier - currA1.index
            f2 = currA2.values + frontier - currA2.index
            while frontier < endIndex1 and frontier < endIndex2:
                result += f1[0] * f2[0]
                f1 += 1
                f2 += 1
                frontier += 1

            if frontier >= endIndex1:
                currA1 = currA1.nextA[0]
                if currA1 == NULL:
                    break
                delta = frontier - currA1.index
                
            if frontier >= endIndex2:
                currA2 = currA2.nextA[0]
                if currA2 == NULL:
                    break
                delta += currA2.index - frontier
                frontier = currA2.index
        return result
        
    cpdef addFast(self, FlexibleVector other, float w):
        cdef SkipNodeA* currA1 = self.head.nextA[0]
        cdef SkipNodeA* currA2 = other.head.nextA[0]
        if currA1 == NULL or currA2 == NULL:
            return
            
        cdef long long frontier = currA2.index
        cdef long long delta = frontier - currA1.index
        cdef long long endIndex1, endIndex2
        cdef float* f1
        cdef float* f2
        while 1:
            endIndex1 = currA1.index + currA1.length
            endIndex2 = currA2.index + currA2.length

            if delta > 0:
                if frontier < endIndex1:
                    delta = 0
                else:
                    delta = frontier - endIndex1
            elif delta < 0:
                if frontier - delta < endIndex2:
                    frontier -= delta
                    delta = 0
                else:
                    delta += endIndex2 - frontier
                    frontier = endIndex2

            f1 = currA1.values + frontier - currA1.index
            f2 = currA2.values + frontier - currA2.index
            while frontier < endIndex1 and frontier < endIndex2:
                f1[0] += f2[0] * w
                f1 += 1
                f2 += 1
                frontier += 1

            if frontier >= endIndex1:
                currA1 = currA1.nextA[0]
                if currA1 == NULL:
                    break
                delta = frontier - currA1.index
                
            if frontier >= endIndex2:
                currA2 = currA2.nextA[0]
                if currA2 == NULL:
                    break
                delta += currA2.index - frontier
                frontier = currA2.index
        return
        
    cpdef add(self, FlexibleVector other, float w):
        cdef SkipNodeA* currA1 = self.head.nextA[0]
        cdef SkipNodeA* currA2 = other.head.nextA[0]
        cdef SkipNodeA* neighbor
        cdef int height
        cdef long i
        cdef long deltaBeg, deltaEnd
        cdef long oldLength
        
        if currA2 == NULL:
            return
        
        while currA2 != NULL:
            self.updateList(currA2.index)
            currA1 = self.found[0].nextA[0]
            if currA1 == NULL:
                break
            deltaBeg = currA1.index - currA2.index
            deltaEnd = currA2.length - currA1.length - deltaBeg
            oldLength = currA1.length
            # compute the new length and index
            if deltaBeg > 0:
                currA1.length += deltaBeg
                currA1.index = currA2.index
            if deltaEnd > 0:
                currA1.length += deltaEnd
            # increase memory if neccessary
            if currA1.length > currA1.capacity:
                currA1.capacity = currA1.length * 2
                currA1.values = <float*>realloc(currA1.values, currA1.capacity * cython.sizeof(float))
                _MEM_CHECK(currA1.values)
            # add
            if deltaBeg > 0:
                # move values
                for i in reversed(xrange(oldLength)):
                    currA1.values[i + deltaBeg] = currA1.values[i]
                for i in xrange(deltaBeg):
                    currA1.values[i] = 0
                deltaBeg = 0
            if deltaEnd > 0:
                # initialize to 0
                for i in xrange(currA1.length - deltaEnd, currA1.length):
                    currA1.values[i] = 0
            for i in xrange(currA2.length):
                currA1.values[i - deltaBeg] += currA2.values[i] * w
            
            if deltaEnd > 0:
                # merge the neighboring node
                neighbor = currA1.nextA[0]
                while neighbor != NULL and neighbor.index <= currA1.index + currA1.length:
                    deltaEnd = neighbor.index - currA1.index
                    deltaBeg = _MIN(neighbor.length, currA1.index + currA1.length - neighbor.index)
                    for i in xrange(deltaBeg):
                        currA1.values[i + deltaEnd] += neighbor.values[i]
                        
                    # copy neighboring values
                    oldLength = currA1.length
                    currA1.length += neighbor.length - deltaBeg
                    if currA1.length > currA1.capacity:
                        currA1.capacity = currA1.length
                        currA1.values = <float*>realloc(currA1.values, currA1.capacity * cython.sizeof(float))
                        _MEM_CHECK(currA1.values)
                    for i in xrange(neighbor.length - deltaBeg):
                        currA1.values[oldLength + i] = neighbor.values[i + deltaBeg]
                    # remove the neighboring node
                    for height in xrange(neighbor.height):
                        if self.found[height].nextA[height] == currA1:
                            currA1.nextA[height] = neighbor.nextA[height]
                        else:
                            self.found[height].nextA[height] = neighbor.nextA[height]
                    _delSkipNodeA(neighbor)
                    self.redueHeight()
                    neighbor = currA1.nextA[0]
            currA2 = currA2.nextA[0]
            
        # copy to the end
        while currA2 != NULL:
            currA1 = _copySkipNodeA(currA2, w)
            if currA1.height > self.height:
                self.height = currA1.height
            for height in xrange(currA1.height):
                self.found[height].nextA[height] = currA1
                self.found[height] = currA1
            currA2 = currA2.nextA[0]
    
    cpdef difference(self, FlexibleVector other, float tol = 1e-8):
        self.add(other, -1)
        self.trim(tol, False)
    
    cpdef matching(self, FlexibleVector other, float tol = 0.01):
        self.add(other, -1)
        self.trim(tol, False)
        self.foreach(_MATCH)

cpdef FlexibleVector difference(FlexibleVector a, FlexibleVector b, float tol = 1e-8):
    cdef FlexibleVector c = FlexibleVector()
    c.add(a,  1)
    c.add(b, -1)
    c.trim(tol, False)
    return c
    
cpdef FlexibleVector matching(FlexibleVector a, FlexibleVector b, float tol = 0.01):
    cdef FlexibleVector c = FlexibleVector()
    c.add(a,  1)
    c.add(b, -1)
    c.trim(tol, False)
    c.foreach(_MATCH)
    return c
