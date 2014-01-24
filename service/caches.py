# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 13:44:37 2013

@author: xumiao
"""
from zope.interface import Interface, Attribute, implements

class ICache(Interface):
    entities = Attribute("A dictionary to store all entities.")
    pandas   = Attribute("A dictionary to store all classifiers.")
    queue    = Attribute("Job queue to store all training jobs.")
    
class Caches(object):
    implements(ICache)
    def __init__(self):
        self.entities = {}
        self.pandas = {}
        self.queue = {}