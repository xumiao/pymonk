# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 18:43:29 2014
A Sum-Product Network for organizing Pandas
@author: pacif_000
"""

from monk.core.monk import *
import monk.core.panda as ppanda
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
        if "children" not in self.__dict__:
            self.children = []
        else:
            self.children = monkFactory.load_or_create_all(ViperStore, self.children)
    
    def __defaults__(self):
        super(PNode, self).__defaults__()
        self.children = []
    
    def generic(self):
        result = super(PNode, self).generic()
        self.appendType(result)
        result["children"] = map(lambda x: x._id, self.children)

class SNode(MONKObject):
    def __restore__(self):
        super(SNode, self)._restore__()
        if "panda" not in self.__dict__:
            self.panda = ppanda.Panda()
        else:
            self.panda = monkFactory.load_or_create(PandaStore, self.panda)
        if "children" not in self.__dict__:
            self.children = []
        else:
            self.children = monkFactory.load_or_create_all(ViperStore, self.children)
    
    def __defaults__(self):
        super(SNode, self).__defaults__()
        self.panda = ppanda.Panda()
        self.children = []
    
    def generic(self):
        result = super(SNode, self).generic()
        self.appendType(result)
        result["panda"] = self.panda._id
        result["children"] = map(lambda x: x._id, self.children)
        
class Viper(MONKObject):
    name = 'Fully factored'
    def __restore__(self):
        super(Viper, self).__restore__()
        if "SPN" not in self.__dict__:
            self.SPN = PNode()
        else:
            self.SPN = monkFactory.load_or_create(ViperStore, self.SPN)
    
    def __defaults__(self):
        super(Viper, self).__defaults__()
        self.SPN = PNode()
        
    def generic(self):
        result = super(Viper, self).generic()
        self.appendType(result)
        result["SPN"] = self.SPN._id

monkFactory.register('PNode', PNode.create)
monkFactory.register('SNode', SNode.create)
monkFactory.register('Viper', Viper.create)