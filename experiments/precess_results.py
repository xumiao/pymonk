# -*- coding: utf-8 -*-
"""
Created on Tue Jul 08 15:04:24 2014

@author: xumiao
"""

import pymongo as pm
from kafka.client import KafkaClient
from kafka.producer import UserProducer
import simplejson
import logging
from monk.math.flexible_vector import FlexibleVector
from random import sample
import pickle
import numpy as np
import matplotlib.pyplot as plt
import re


def parse_log_file(filename):
    objectives = {}
    current_user = None
    with open(filename) as fn:
        for line in fn:
            print line
            match = re.search('difference of user ([\w-]*)', line)
            if match:
                current_user = match.groups()[0]
                if current_user not in objectives:
                    objectives[current_user] = []
                continue
            
            match = re.search('objective = ([\d.]+)', line)
            if match:
                value = float(match.groups()[0])
                objectives[current_user].append(value)
    return objectives
    
def plot_obj_curves(objectives):
    for user in objectives.keys():
        values = objectives[user]
        values = [values[i] for i in range(0, len(values), 2)]
        plt.plot(range(len(values)), values)