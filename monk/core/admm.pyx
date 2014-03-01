# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 13:59:53 2013

@author: xumiao
"""

from __future__ import division

import numpy as np
cimport numpy as np
cimport cython
from libc.stdlib cimport malloc, free, calloc
#cdef extern from "math.h":
#    float max(float v1, float v2)
#    float min(float v1, float v2)

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
    
ctypedef int* int_type_t 
ctypedef float* float_type_t
ctypedef float** float_type2_t

cdef class ADMMsvc(object):
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
    
    def __init__(self, data = {}, eps = 1e-4, Cp = 1, Cn = 1, lam = 1, max_iter = 1000, rho = 10):
        cdef int i
        cdef int j
        cdef int k
        self.users = {}
        self.userList = []
        self.M = len(data)
        if self.M == 0:
            self.y = NULL
            self.x = NULL
            self.L = NULL
            self.index = NULL
            self.QD = NULL
            self.alpha = NULL
            self.w = NULL
            self.z = NULL
            self.xmin = NULL
            self.xmax = NULL
            return

        self.nf = data.values()[0].shape[1] - 1
        self.L = <int*>malloc(self.M * cython.sizeof(int))
        self.index = <int**>malloc(self.M * cython.sizeof(int_type_t))
        self.y = <int**>malloc(self.M*cython.sizeof(int_type_t))
        self.x = <float***>malloc(self.M*cython.sizeof(float_type2_t))
        self.QD = <float**>malloc(self.M*cython.sizeof(float_type_t))
        self.alpha = <float**>malloc(self.M*cython.sizeof(float_type_t))
        self.w = <float**>malloc(self.M*cython.sizeof(float_type_t))
        self.z = <float*>malloc((self.nf)*cython.sizeof(float))
        self.xmin = <float*>malloc(self.nf * cython.sizeof(float))
        self.xmax = <float*>malloc(self.nf * cython.sizeof(float))
        for k in xrange(self.nf):
            self.xmin[k] = 1e6
            self.xmax[k] = -1e6
        
        kvps = data.items()
        for i in xrange(self.M):
            kvp = kvps[i]
            self.users[kvp[0]] = i
            self.userList.append(kvp[0])
            userdata = kvp[1]
            self.L[i] = userdata.shape[0]
            self.y[i] = <int*>malloc(self.L[i] * cython.sizeof(int))
            self.x[i] = <float**>malloc(self.L[i] * cython.sizeof(float_type_t))
            self.index[i] = <int*>malloc(self.L[i] * cython.sizeof(int))
            self.w[i] = <float*>malloc((self.nf) * cython.sizeof(float))
            self.alpha[i] = <float*>malloc(self.L[i] * cython.sizeof(float))
            self.QD[i] = <float*>malloc(self.L[i] * cython.sizeof(float))
            for j in xrange(self.L[i]):
                self.index[i][j] = j
                self.y[i][j] = userdata[j][-1]
                if (self.y[i][j] > 0):
                    pos += 1
                else:
                    neg += 1
                self.x[i][j] = <float*>malloc(self.nf * cython.sizeof(float))
                for k in xrange(self.nf):
                    self.x[i][j][k] = userdata[j][k]
                    self.xmin[k] = min(self.x[i][j][k], self.xmin[k])
                    self.xmax[k] = max(self.x[i][j][k], self.xmax[k])
             
        self.eps = eps
        self.Cp = Cp * neg / pos
        self.Cn = Cn
        self.lam = lam
        self.max_iter = max_iter
        self.rho = rho

    cdef _free_data(self):
        cdef int i,j
        for i in xrange(self.M):
            for j in xrange(self.L[i]):
                free(self.x[i][j])
            free(self.x[i])
            free(self.y[i])
            free(self.index[i])
            free(self.QD[i])
            free(self.alpha[i])
        free(self.x)
        free(self.y)
        free(self.index)
        free(self.QD)
        free(self.alpha)
        free(self.L)
    
    cdef _free_model(self):
        cdef int i
        for i in xrange(self.M):
            free(self.w[i])
        free(self.xmin)
        free(self.xmax)
        free(self.w)
        free(self.z)
        
    def __del__(self):
        if self.L:
            self._free_data()
        if self.z:
            self._free_model()
    
    cdef inline scale(self, v, xmin, xmax):
        if xmax - xmin >= 1e-4:
            return (2 * v - xmin - xmax) / (xmax - xmin)
        else:
            return v

    cpdef uniformize(self):
        cdef int i,k
        for i in xrange(self.M):
            for k in xrange(self.nf):
                self.w[i][k] = 1
        for k in xrange(self.nf):
            self.z[k] = 1
            self.xmin[k] = 0
            self.xmax[k] = 0
        
    cpdef initialization(self):
        cdef int i,j,k
        for i in xrange(self.M):
            for j in xrange(self.L[i]):
                self.alpha[i][j] = 0
                self.index[i][j] = j
                if self.y[i][j] > 0:
                    self.QD[i][j] = 0.5 * self.rho / self.Cp
                else:
                    self.QD[i][j] = 0.5 * self.rho / self.Cn
                for k in xrange(self.nf):
                    self.x[i][j][k] = self.scale(self.x[i][j][k], self.xmin[k], self.xmax[k])
                    self.QD[i][j] += self.x[i][j][k] * self.x[i][j][k]
            for k in xrange(self.nf):
                self.w[i][k] = 0
        for k in xrange(self.nf):
            self.z[k] = 0
    
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
        
    cpdef trainOne(self, int i):
        cdef int l = self.L[i]
        cdef int nf = self.nf
        cdef int j, k, s, iteration
        cdef float ya, d, G, alpha_old
        cdef int active_size = l
        cdef float* w = self.w[i]
        cdef int* index = self.index[i]
        cdef float* alpha = self.alpha[i]
        cdef int* y = self.y[i]
        cdef float** x = self.x[i]
        cdef float* QD = self.QD[i]
        cdef int yj
        cdef float* xj
    
        # PG: projected gradient, for shrinking and stopping
        cdef float PG
        cdef float PGmax_old = 1e10
        cdef float PGmin_old = -1e10
        cdef float PGmax_new
        cdef float PGmin_new
        
        for k in xrange(nf):
            w[k] = self.z[k]
         
        for j in xrange(l):
            index[j] = j
            ya = y[j] * alpha[j]
            for k in xrange(nf):
                w[k] += ya * x[j][k]

        iteration = 0
        while iteration < self.max_iter:
            PGmax_new = -1e10
            PGmin_new = 1e10
            
            for j in xrange(active_size):
                k = j + int(np.random.rand() * (active_size - j))
                self.swap(index, j, k)

            for s in xrange(active_size):
                j = index[s]
                yj = y[j]
                xj = x[j]
                
                G = 0
                for k in xrange(nf):
                    G += w[k] * xj[k]

                G = G * yj - 1
                
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
                    for k in xrange(nf):
                        w[k] += d * xj[k]
                        
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

    cpdef train(self, int num):
        cdef int i, iteration, k
        cdef float* w
        self.initialization()
        for iteration in xrange(num):
            print 'iter = ',iteration
            for i in xrange(self.M):
                self.status(i)
                self.trainOne(i)
                self.status(i)
            # averaging w for z
                
            for k in xrange(self.nf):
                self.z[k] = 0
            for i in xrange(self.M):
                w = self.w[i]
                for k in xrange(self.nf):
                    self.z[k] += w[k]
            for k in xrange(self.nf):
                self.z[k] /= self.M + 1 / self.rho
            
            # additional updates for the dual variables
    
    cpdef test(self, data, fileName, enablePersonalization):
        cdef float* fp = <float*>calloc(self.M + 1, cython.sizeof(float))
        cdef float* fn = <float*>calloc(self.M + 1, cython.sizeof(float))
        cdef float* tp = <float*>calloc(self.M + 1, cython.sizeof(float))
        cdef float* tn = <float*>calloc(self.M + 1, cython.sizeof(float))
        cdef int M = len(data)
        cdef int i, j, k, s
        cdef int L,LM
        cdef float x, G, totalFP, totalFN, totalTP, totalTN, totalL
        cdef float* w
        f = file(fileName, 'w')
        fResult = file(fileName + ".result", 'w')
        fGroundTruth = file(fileName + ".gt", 'w')
        kvps = data.items()
        LM = 0
        totalFP = 0
        totalFN = 0
        totalTP = 0
        totalTN = 0
        totalL = 0
        for s in xrange(M):
            kvp = kvps[s]
            if kvp[0] not in self.users:
                i = self.M
                w = self.z
            else:
                i = self.users[kvp[0]]
                if enablePersonalization:
                    w = self.w[i]
                else:
                    w = self.z
            userdata = kvp[1]
            L = userdata.shape[0]
            for j in xrange(L):
                G = 0
                for k in xrange(self.nf):
                    G += w[k] * self.scale(userdata[j][k], self.xmin[k], self.xmax[k])
                
                if G > 0:
                    if userdata[j][-1] > 0:
                        tp[i] += 1
                    else:
                        fp[i] += 1
                else:
                    if userdata[j][-1] > 0:
                        fn[i] += 1
                    else:
                        tn[i] += 1
                if( j < L-1):
                    fResult.write(str(G)+'\t')
                    fGroundTruth.write(str(userdata[j][-1])+'\t')
                else:
                    fResult.write(str(G)+'\n')
                    fGroundTruth.write(str(userdata[j][-1])+'\n')    
            o = 'TP:{0:.4f} TN:{1:.4f} FP:{2:.4f} FN:{3:.4f} {4}'.format(tp[i] / L, tn[i] / L, fp[i] / L, fn[i] / L, kvp[0])
            print o
            f.write(o + '\n')
            totalFP += fp[i]
            totalFN += fn[i]
            totalTP += tp[i]
            totalTN += tn[i]
            totalL += L

        o = 'totalTP:{0:.4f} totalTN:{1:.4f} totalFP:{2:.4f} totalFN:{3:.4f}'.format(totalTP / totalL, totalTN / totalL, totalFP / totalL, totalFN / totalL)
        print o
        f.write(o + '\n')
        fResult.close()
        fGroundTruth.close()
        f.close()
        free(fp)
        free(fn)
        free(tp)
        free(tn)
    

    def getScales(self):
        cdef int i
        if self.xmin == NULL or self.xmax == NULL:
            return np.array([]), np.array([])
            
        xmin = np.zeros(self.nf)
        xmax = np.zeros(self.nf)
        for i in xrange(self.nf):
            xmin[i] = self.xmin[i]
            xmax[i] = self.xmax[i]
        return xmin, xmax
        
    cpdef saveModel(self, fileName):
        cdef int i, j, k
        cdef int nf1 = self.nf -1 
        f = file(fileName, 'w')
        f.write('# number of features\n')
        f.write(str(self.nf) + '\n')
        f.write('# number of users\n')
        f.write(str(self.M) + '\n')
        f.write('# scale minimun\n')
        for k in xrange(nf1):
            f.write(str(self.xmin[k]) + ' , ')
        f.write(str(self.xmin[nf1]) + '\n')
        f.write('# scale maximun\n')
        for k in xrange(nf1):
            f.write(str(self.xmax[k]) + ' , ')
        f.write(str(self.xmax[nf1]) + '\n')
        f.write('# population model\n')
        for k in xrange(nf1):
            f.write(str(self.z[k]) + ' , ')
        f.write(str(self.z[nf1]) + '\n')
        f.write('# individual models\n')
        for i in xrange(self.M):
            user = self.userList[i]
            f.write(user + '\n')
            for k in xrange(nf1):
                f.write(str(self.w[i][k]) + ' , ')
            f.write(str(self.w[i][nf1]) + '\n')
        f.close()
        
    cpdef loadModel(self, fileName):
        cdef int i,j,k
        f = file(fileName, 'r')
        f.readline()
        self.nf = int(f.readline())
        f.readline()
        self.M = int(f.readline())
        
        self.w = <float**>malloc(self.M * cython.sizeof(float_type_t))
        self.z = <float*>malloc(self.nf * cython.sizeof(float))
        self.xmin = <float*>malloc(self.nf * cython.sizeof(float))
        self.xmax = <float*>malloc(self.nf * cython.sizeof(float))
        
        f.readline()
        strs = f.readline().split(' , ')
        for k in xrange(self.nf):
            self.xmin[k] = float(strs[k])
        
        f.readline()
        strs = f.readline().split(' , ')
        for k in xrange(self.nf):
            self.xmax[k] = float(strs[k])
        
        f.readline()
        strs = f.readline().split(' , ')
        for k in xrange(self.nf):
            self.z[k] = float(strs[k])
        
        f.readline()
        for i in xrange(self.M):
            self.w[i] = <float*>malloc(self.nf * cython.sizeof(float))
            user = f.readline()[:-1]
            self.users[user] = i
            self.userList.append(user)
            strs = f.readline().split(' , ')
            for k in xrange(self.nf):
                self.w[i][k] = float(strs[k])
                
    cpdef evaluate(self, resultFileName, gtFileName):                
        numLines = 0
        with open(gtFileName) as f:
            for line in f:
                numLines = numLines + 1
        fResult = file(resultFileName, 'r')
        fGroundTruth = file(gtFileName, 'r')
        resGT = []
        
        print "number of " + str(numLines) #str(self.M)
        totalP = 0
        totalN = 0
        for m in xrange(numLines): #while(len(strsResult) != 0): 
            print "m = " + str(m)
            strsResult = fResult.readline().split('\t')
            strsGroundTruth = fGroundTruth.readline().split('\t')
            print "len(strsResult) = " + str(len(strsResult))
            print "len(strsGroundTruth) = " + str(len(strsGroundTruth))
            for k in xrange(len(strsResult)):
                print str(k) + " = " + strsResult[k]
                resGT.append((float(strsResult[k]), float(strsGroundTruth[k])))                   
                if(float(strsGroundTruth[k]) > 0):
                    totalP = totalP + 1
                else:
                    totalN = totalN + 1                  
        resGT.sort()    
        print "totalP = " + str(totalP)
        print "totalN = " + str(totalN)
        if(totalP + totalN != len(resGT)):
            print "the number of samples are not consistent\n"
        else:
            print "the number of samples are consistent\n"

        fCurve = file(resultFileName[:-7] + ".curve", 'w')
        fCurve.write('threshold\tPrecision\tRecall\tFPrate\n')
        totalFP = totalN
        totalFN = 0
        totalTP = totalP
        totalTN = 0   
        numberOfCurve = 500        
        minVal = float(resGT[0][0])
        maxVal = float(resGT[-1][0])
        thre = np.linspace(minVal, maxVal, numberOfCurve)
        k = 0
        for i in xrange(numberOfCurve):
            while(float(resGT[k][0]) < thre[i]):                
                if(float(resGT[k][1]) < 0):
                    totalTN = totalTN + 1
                else:
                    totalFN = totalFN + 1
                k = k + 1                    
            totalFP = totalN - totalTN
            totalTP = totalP - totalFN
            
            if(totalTP+totalFP == 0):
                precision = 1
            else:
                precision = totalTP / (totalTP+totalFP)                              
            if(totalP == 0):
                recall = 0
            else:
                recall = totalTP / totalP                              
            if(totalN == 0):
                FPrate = 0
            else:
                FPrate = totalFP / totalN       
            o = '{0:.8f}\t{1:.8f}\t{2:.8f}\t{3:.8f}'.format(thre[i], precision, recall, FPrate)            
            fCurve.write(o + '\n')
        
        fCurve.close()
        fGroundTruth.close()
        fResult.close()
            
            
            
            
            
            