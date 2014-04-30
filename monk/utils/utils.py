# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 10:44:50 2013

@author: xumiao
"""

import pickle
import StringIO

import simplejson
import datetime
from IPython.core.display import Image
import logging

logger = logging.getLogger('monk.utils')

class DateTimeEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)

def show(ent, fields=[], imgField=None):
    ret = ent.generic()
    if not fields:
        print simplejson.dumps(ret, indent=4, cls=DateTimeEncoder)
    else:
        print simplejson.dumps({field: ret.get(field, "") for field in fields}, indent=4, cls=DateTimeEncoder)
    
    if imgField:
        try:
            return Image(url=ret.get(imgField, ""))
        except Exception as e:
            logger.info('can not display image {0}'.format(e.message))
    return None

def translate(self, obj, sep=' '):
    try:
        ret = ""
        if isinstance(obj, basestring):
            ret = obj
        else:
            ret = sep.join(obj)
        return ret.decode('utf-8')
    except Exception as e:
        logger.info('{0}'.format(e.message))
        logger.info('error in tranlating {0}'.format(obj))
        logger.info('unknow value formats')
        return None

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
