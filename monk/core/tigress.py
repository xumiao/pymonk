# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:53:08 2013
A superviser to break down problems into binary ones to solve. 
The inducer is based on SPN (sum product network) to form the reduction rules.

@author: xm
"""

from base import MONKObject, monkFactory


class Tigress(MONKObject):
    name = 'Negative tigress'
    description = 'Always assigns to the negative class'

    def __restore__(self):
        super(Tigress, self).__restore__()
        if "pCuriosity" not in self.__dict__:
            self.pCuriosity = 0.0

    def __defaults__(self):
        super(Tigress, self).__defaults__()
        self.pCuriosity = 0.0

    def generic(self):
        result = super(Tigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass


class PatternTigress(Tigress):
    name = 'Pattern tigress'
    description = 'Assign positive when a pattern matched'

    def __restore__(self):
        super(PatternTigress, self).__restore__()
        if 'pattern' not in self.__dict__ or 'fields' not in self.__dict__:
            raise Exception('No pattern or fields specified')

    def __defaults__(self):
        super(PatternTigress, self).__defaults__()
        self.pattern = ''
        self.fields = []

    def generic(self):
        result = super(PatternTigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass


class SelfTigress(Tigress):
    name = 'Self supervising tigress'
    description = 'Supervising by predicting first'

    def generic(self):
        result = super(SelfTigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass


class SPNTigress(Tigress):
    name = 'SPN inducer'
    description = 'Induce SPN from data'

    def generic(self):
        result = super(SPNTigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass


class LexiconTigress(Tigress):
    name = 'Lexicon inducer'
    description = 'Induce lexicon from data'

    def generic(self):
        result = super(LexiconTigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass


class ActiveTigress(Tigress):
    name = 'Active learner'
    description = 'Actively query human experts'

    def generic(self):
        result = super(ActiveTigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass


class CoTigress(Tigress):
    name = 'Cotrainer'
    description = 'Cotraining by supervising with multiple sources'

    def generic(self):
        result = super(CoTigress, self).generic()
        self.appendType(result)

    def supervise(self, viper, entity):
        pass

monkFactory.register(Tigress)
monkFactory.register(PatternTigress)
monkFactory.register(SelfTigress)
monkFactory.register(SPNTigress)
monkFactory.register(LexiconTigress)
monkFactory.register(ActiveTigress)
monkFactory.register(CoTigress)
