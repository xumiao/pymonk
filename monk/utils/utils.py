# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 10:44:50 2013

@author: xumiao
"""

import pickle
import StringIO
import simplejson
import datetime
import time
from IPython.core.display import Image
import logging
from monk.core.constants import EPS
from monk.math.flexible_vector import difference
from numpy import sqrt
import importlib
from simplejson import encoder
encoder.FLOAT_REPR = lambda o: format(o, '.4f')

logger = logging.getLogger('monk.utils.utils')


import os
import socket

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

def get_host_name(address=None, pid=None):
    if not address:
        address = get_lan_ip()
    if not pid:
        pid = os.getpid()
    return '{}-{}'.format(address, pid)

def class_from(moduleName, className):
    m = importlib.import_module(moduleName)
    c = getattr(m, className)
    return c
    
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

def currentTimeMillisecond():
    t = datetime.datetime.now()
    return time.mktime(t.timetuple()) * 1e3 + t.microsecond / 1e3

def jsonMetric(monkobj, name, value):
    return simplejson.dumps({"user":monkobj.creator,
                             "time":currentTimeMillisecond(),
                             name:value})
                            
def encodeMetric(monkobj, name, value):
    return 'user={0},time={1},{2}={3}'.format(
            monkobj.creator, currentTimeMillisecond(), name, value)

def decodeMetric(message):
    body = message.split(',')
    # user 
    monkuser = body[0].split('=')[1]
    # time
    t = float(body[1].split('=')[1])
    # metric
    name = body[2].split('=')[0]
    value = float(body[2].split('=')[1])
    return monkuser, t, name, value

def metricValue(metricLogger, monkobj, name, v):
    #metricLogger.info(encodeMetric(monkobj, name, v))
    metricLogger.info(jsonMetric(monkobj, name, v))
    
def metricAbs(metricLogger, monkobj, name, v):
    #metricLogger.info(encodeMetric(monkobj, name, v.norm()))
    metricLogger.info(jsonMetric(monkobj, name, v.norm()))
    
def metricRelAbs(metricLogger, monkobj, name, v1, v2):
    dv = difference(v1, v2)
    #metricLogger.info(encodeMetric(monkobj, name, sqrt((dv.norm2() + EPS) / (v1.norm() * v2.norm() + EPS))))
    metricLogger.info(jsonMetric(monkobj, name, sqrt((dv.norm2() + EPS) / (v1.norm() * v2.norm() + EPS))))
    del dv
    
def binary2decimal(a):
    return reduce(lambda x,y: (x + y) << 1, 0) / 2
    
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

def translate(obj, sep=' '):
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
