# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 18:43:29 2014
A Sum-Product Network for organizing Pandas
@todo: need more work
@author: pacif_000
"""

"""
from ..core.base import MONKObject
import ..core.panda as ppanda

An example of SPN
{
'children':[
    {
    'panda':
        {
        '_type':['LinearPanda'],
        'name':'test1',
        ...
        }
    },
    {
    'panda':
        {
        '_type':['LinearPanda'],
        'name':'test2',
        ...
        }
    }
]}


class PNode(MONKObject):

    def __restore__(self):
        super(PNode, self).__restore__()
        if "children" not in self.__dict__:
            self.children = []
        else:
            for child in self.children:
                if "_type" not in child:
                    child["_type"] = ["SNode"]
            self.children = viperStore.load_or_create_all(self.children)

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
            self.panda = pandaStore.load_or_create(self.panda)
        if "children" not in self.__dict__:
            self.children = []
        else:
            self.children = viperStore.load_or_create_all(self.children)

    def __defaults__(self):
        super(SNode, self).__defaults__()
        self.panda = ppanda.Panda()
        self.children = []

    def generic(self):
        result = super(SNode, self).generic()
        self.appendType(result)
        result["panda"] = self.panda._id
        result["children"] = map(lambda x: x._id, self.children)
"""
        