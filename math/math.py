# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 15:44:59 2013

@author: xm
"""
import numpy as np
def sigmoid(v):
    v = np.exp(v)
    return (v - 1/v) / (v + 1/v)