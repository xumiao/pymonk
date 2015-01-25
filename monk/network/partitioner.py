# -*- coding: utf-8 -*-
"""
Created on Sun Oct  5 14:38:22 2014

@author: xm
"""

import logging
from kafka.partitioner.base import Partitioner
import monk.core.api as monkapi
from itertools import cycle

logger = logging.getLogger('monk.network.partitioner')

class UserPartitioner(Partitioner):
    """
    With fixed partition output for the key (user)
    Assumption: monkapi is initialized first
    """
    def __init__(self, partitions=[0]):
        """
        Initialize the partitioner
        partitions - A list of available partitions to round robin when no partition found for the user
        """
        self._set_partition(partitions)
            
    def _set_partition(self, partitions):
        self.partitions = partitions
        if partitions:
            self.iterpart = cycle(partitions)        
        else:
            self.iterpart = cycle([0])
            
    def partition(self, key, partitions=None):
         # Refresh the partition list if necessary
        if partitions and self.partitions != partitions:
            self._set_partitions(partitions)
        logger.debug('key {}'.format(key))
        user = monkapi.load_user(key)
        if not user:
            return self.iterpart.next()
        else:
            return user.partition
        