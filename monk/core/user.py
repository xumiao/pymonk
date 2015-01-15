# -*- coding: utf-8 -*-
"""
Created on Sun Sep 28 09:17:38 2014

@author: xm
"""
import base
import crane
import datetime
from constants import DEFAULT_NONE, DEFAULT_EMPTY
import logging

logger = logging.getLogger("monk.user")

class User(base.MONKObject):
    FPASSWORD = 'password'
    FGENDER   = 'gender'
    FYEAR     = 'year'
    FPART     = 'partition'
    FTURTLES  = 'turtles'
    FFNAME    = 'firstName'
    FLNAME    = 'lastName'
    FMName    = 'midName'
    
    store = crane.userStore
    
    def __default__(self):
        super(User, self).__default__()
        self.password = DEFAULT_EMPTY
        self.gender = DEFAULT_NONE
        self.firstName = DEFAULT_EMPTY
        self.lastName = DEFAULT_EMPTY
        self.midName = DEFAULT_EMPTY
        self.year = 1900
        self.partition = -1
        self.turtles = []
        
    def __restore__(self):
        super(User, self).__restore__()
        
    def generic(self):
        result = super(User, self).generic()
        return result

    def clone(self, userName):
        ''' User can not be replicated '''
        return None
    
    def age(self):
        thisyear = datetime.date.today().year
        return thisyear - self.year
    
    def set_partition(self, partition):
        self.partition = partition
        self.update_fields({self.PART:self.partition})
    
    def add_turtle(self, turtleName):
        self.turtles.append(turtleName)
        self.store.push_one_in_fields(self, {self.FTURTLES: turtleName})
        
base.register(User)