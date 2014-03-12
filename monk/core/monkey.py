# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:30 2013
The evaluator that measures the performance and the accuracy of a turtle
@author: xm
"""
from monk.core.base import MONKObject, monkFactory

class Monkey(MONKObject):

    def __restore__(self):
        super(Monkey, self).__restore__()

    def __defaults__(self):
        super(Monkey, self).__defaults__()

    def generic(self):
        result = super(Monkey, self).generic()
        self.appendType(result)

monkFactory.register(Monkey)
