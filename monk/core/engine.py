# -*- coding: utf-8 -*-
"""
Created on Wed Oct  1 00:16:27 2014

@author: xm
"""

import base
import crane
import datetime
import time
import constants as cons
import logging

logger = logging.getLogger("monk.engine")

class Engine(base.MONKObject):
    IDLE_TIME   = 1200 # 20 minutes
    FADDRESS    = 'address'
    FPID        = 'pid'
    FPARTITION  = 'partition'
    FSTATUS     = 'status'
    FUSERS      = 'users'
    FSTARTTIME  = 'starttime'
    FENDTIME    = 'endtime'
    
    store = crane.engineStore
    
    def __default__(self):
        super(Engine, self).__default__()
        self.address = cons.DEFAULT_EMPTY
        self.pid = cons.DEFAULT_EMPTY
        self.partition = 0
        self.status = cons.STATUS_INACTIVE
        self.starttime = datetime.datetime.now()
        self.endtime = datetime.datetime.now()
        self.users = []
        
    def __restore__(self):
        super(Engine, self).__restore__()
        
    def generic(self):
        result = super(Engine, self).generic()
        result[self.FSTARTTIME] = self.starttime
        result[self.FENDTIME] = self.endtime
        return result

    def clone(self, userName):
        ''' Engine can not be replicated '''
        return None
    
    def is_active(self):
        if not self.status:
            return False
        currTime = time.mktime(datetime.datetime.now().timetuple())
        lastTime = time.mktime(self.lastModified.timetuple())
        logger.debug('currTime={}, lastTime={}, idleTime={}'.format(currTime, lastTime, self.IDLE_TIME))
        if currTime - lastTime > self.IDLE_TIME:
            self.status = cons.STATUS_INACTIVE
            self.update_fields({self.FSTATUS:cons.STATUS_INACTIVE})
            return False
        return True
        
    def add_user(self, userName):
        self.users.append(userName)
        self.store.push_one_in_fields(self, {self.FUSERS:userName})
        
base.register(Engine)