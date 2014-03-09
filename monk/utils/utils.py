# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 10:44:50 2013

@author: xumiao
"""

import pickle
import StringIO


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
