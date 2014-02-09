# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 18:43:29 2014
A Sum-Product Network for organizing Pandas
@author: pacif_000
"""

from pymonk.core.monk import *
"""
An example of SPN
{
'_type':['PNode'],
'children':[
    {
    '_type':['SNode'],
    'panda':
        {
        '_type':['Panda'],
        'name':'test1',
        ...
        }
    },
    {
    '_type':['SNode'],
    'panda':
        {
        '_type':['Panda'],
        'name':'test2',
        ...
        }
    }
]}
"""

class PNode(MONKObject):
    def __restore__(self):
        super(PNode, self).__restore__()
        self.children = monkFactory.load_or_create_all(ViperStore, self.children)
    
    def __defaults__(self):
        super(PNode, self).__defaults__()
        self.children = []
    
    def generic(self):
        result = super(PNode, self).generic()
        self.appendType(result)
        self.children = map(lambda x: x._id, self.children)

class SNode(MONKObject):
    def __restore__(self):
        super(SNode, self)._restore__()
        self.panda = monkFactory.load_or_create(PandaStore, self.panda)
        self.children = monkFactory.load_or_create_all(ViperStore, self.children)
    
    def __defaults__(self):
        super(SNode, self).__defaults__()
        self.children = []
    
    def generic(self):
        result = super(SNode, self).generic()
        self.appendType(result)
        self.children = map(lambda x: x._id, self.children)
        
class Viper(MONKObject):
    def __restore__(self):
        super(Viper, self).__restore__()
        self.SPN = monkFactory.load_or_create(ViperStore, self.SPN)
    
    def __defaults__(self):
        super(Viper, self).__defaults__()
        self.name = 'Fully Factored'
        self.description = 'All decisions are made independently'
        self.SPN = PNode()
        
    def generic(self):
        result = super(Viper, self).generic()
        self.appendType(result)
        self.SPN = self.SPN._id
        