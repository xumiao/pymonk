# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 10:44:50 2013

@author: xumiao
"""

import pickle, StringIO
from twisted.python import log

def GetOrDefault(a, key, default, convert=lambda x: x):
    try:
        r = a[key]
        if type(r) == list:
            return convert(r[0])
        else:
            return convert(r)
    except Exception as e:
        log.msg(e)
        return default
            
def Serialize(a):
    try:
        outfile = StringIO.StringIO()
        pickle.dump(a, outfile)
        return outfile.getvalue()
    except:
        return ""

def Deserialize(astr):
    try:
        infile = StringIO.StringIO(astr)
        return pickle.load(infile)
    except:
        return None

def LowerFirst(astr):
    if astr:
        return astr[:1].lower() + astr[1:]
    else:
        return None

def GetIds(objs):
    map(lambda x: x._id, objs)
    