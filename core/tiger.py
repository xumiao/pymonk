# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:53:08 2013
A superviser to break down problems into binary ones to solve. 
It is based on SPN (sum product network) to formulate the reduction rules.
@author: xm
"""
from pymonk.core.monk import *
from pymonk.utils.utils import GetIds
from datetime import datetime
from bson.objectid import ObjectId
from pymonk.math import sigmoid

class Tiger(MONKObject):
    def __restore__(self):
        super(Tiger, self).__restore__()
    
    def __defaults__(self):
        super(Tiger, self).__defaults__()
        self.name = 'Negative tiger'
        self.description = 'Always assigns negative class'
        self.pCuriosity = 0.0

    def generic(self):
        result = super(Tiger, self).generic()
        result['_type'].append('Tiger')
    
    def label(self, entity):
        return -1
    
class PatternTiger(Tiger):
    def __restore__(self):
        super(PatternTiger, self).__restore__()
        if 'pattern' not in self.__dict__ or 'fields' not in self.__dict__:
            raise Exception('No pattern or fields specified')
            
    def __defaults__(self):
        super(PatternTiger, self).__defaults__()
        self.name = 'Pattern tiger'
        self.description = 'Assign positive when a pattern matched'
        self.pattern = ''
        self.fields = []
    
    def generic(self):
        result = super(PatternTiger, self).generic()
        result['_type'].append('PatternTiger')
    
    def label(self, entity):
        