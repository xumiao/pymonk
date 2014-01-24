# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 08:48:12 2013

@author: xm
"""

def matches(x, ent):
    hist = 0
    try:
        if x in ent["comment"]:
            hist += 1
        elif x in ent["title"]:
            hist += 1
        elif x in ent["desc"]:
            hist += 1
    except:
        pass
    return hist
    
def scoring(ent, soft):
    return reduce(lambda x, y: x + matches(y, ent), soft, 0)
    