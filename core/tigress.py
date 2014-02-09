# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:53:08 2013
A superviser to break down problems into binary ones to solve. 
The inducer is based on SPN (sum product network) to form the reduction rules.

@author: xm
"""
from pymonk.core.monk import *

class Tigress(MONKObject):
    def __restore__(self):
        super(Tigress, self).__restore__()
    
    def __defaults__(self):
        super(Tigress, self).__defaults__()
        self.name = 'Negative tigress'
        self.description = 'Always assigns to the negative class'
        self.pCuriosity = 0.0

    def generic(self):
        result = super(Tigress, self).generic()
        self.appendType(result)
    
    def supervise(self, viper, entity):
        pass
    
class PatternTigress(Tigress):
    def __restore__(self):
        super(PatternTigress, self).__restore__()
        if 'pattern' not in self.__dict__ or 'fields' not in self.__dict__:
            raise Exception('No pattern or fields specified')
            
    def __defaults__(self):
        super(PatternTigress, self).__defaults__()
        self.name = 'Pattern tigress'
        self.description = 'Assign positive when a pattern matched'
        self.pattern = ''
        self.fields = []
    
    def generic(self):
        result = super(PatternTigress, self).generic()
        self.appendType(result)
    
    def supervise(self, viper, entity):
        pass

class SelfTigress(Tigress):
    def __restore__(self):
        super(SelfTigress, self).__restore__()
            
    def __defaults__(self):
        super(SelfTigress, self).__defaults__()
        self.name = 'Self supervising tigress'
        self.description = 'Supervising by predicting first'
    
    def generic(self):
        result = super(SelfTigress, self).generic()
        self.appendType(result)
    
    def supervise(self, viper, entity):
        pass

class SPNTigress(Tigress):
    def __restore__(self):
        super(SPNTigress, self).__restore__()
    
    def __defaults__(self):
        super(SPNTigress, self).__defaults__()
        self.name = 'SPN inducer'
        self.description = 'Induce SPN from data'
    
    def generic(self):
        result = super(SPNTigress, self).generic()
        self.appendType(result)
    
    def supervise(self, viper, entity):
        pass

class LexiconTigress(Tigress):
    def __restore__(self):
        super(LexiconTigress, self).__restore__()
    
    def __defaults__(self):
        super(LexiconTigress, self).__defaults__()
        self.name = 'Lexicon inducer'
        self.description = 'Induce lexicon from data'
    
    def generic(self):
        result = super(LexiconTigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass

class DistanceTigress(Tigress):
    def __restore__(self):
        super(DistanceTigress, self).__restore__()
    
    def __defaults__(self):
        super(DistanceTigress, self).__defaults__()
        self.name = 'Distance supervision'
        self.description = 'Distance supervision'
    
    def generic(self):
        result = super(DistanceTigress,self).generic()
        self.appendType(result)
    
    def supervise(self, viper, entity):
        pass

class ActiveTigress(Tigress):
    def __restore__(self):
        super(ActiveTigress, self).__restore__()
    
    def __defaults__(self):
        super(ActiveTigress, self).__defaults__()
        self.name = 'Active learner'
        self.description = 'Actively query human experts'
    
    def generic(self):
        result = super(ActiveTigress, self).generic()
        self.appendType(result)
    
    def supervise(self, viper, entity):
        pass

class CoTigress(Tigress):
    def __restore__(self):
        super(CoTigress, self).__restore__()
    
    def __defaults__(self):
        super(CoTigress, self).__defaults__()
        self.name = 'Cotrainer'
        self.description = 'Cotraining by supervising with multiple sources'
    
    def generic(self):
        result = super(CoTigress, self).generic()
        self.appendType(result)
    
    def supervise(self, viper, entity):
        pass

monkFactory.register("Tigress", Tigress.create)
monkFactory.register("PatternTigress", PatternTigress.create)
monkFactory.register("SelfTigress", SelfTigress.create)
monkFactory.register("SPNTigress", SPNTigress.create)
monkFactory.register("LexiconTigress", LexiconTigress.create)
monkFactory.register("ActiveTigress", ActiveTigress.create)
monkFactory.register("DistanceTigress", DistanceTigress.create)
monkFactory.register("CoTigress", CoTigress.create)