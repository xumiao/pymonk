# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 16:05:27 2013

@author: xm
"""

import httplib2
import simplejson

#BASEURL = 'http://www.monklearning.com:8080/yelp.rpy'
BASEURL = 'http://www.monklearning.com:8080/tryme.rpy'
def testRecommend():
    testdata = {"hard": {"geo":{"x":47,"y":-122,"d":200}, "datetimeRange": {"start":'2010',"end":'2011'}, "budget":{"min":4,"max":5.1}}, "soft":['holy grail']}
    URL = '{0}/recommend'.format(BASEURL)
    
    jsondata = simplejson.dumps(testdata)
    h = httplib2.Http()
    resp, content = h.request(URL,
                              'POST',
                              jsondata,
                              headers={'Content-Type': 'application/json'})
    print resp
    print content

def testLike():
    testdata = {"query": {"hard": {"geo":{"x":47,"y":-122,"d":200}, "datetimeRange": {"start":'2010',"end":'2011'}, "budget":{"min":4,"max":5.1}}, "soft":['holy grail']},
                "id":"524c04c4e291973e11364ad4"}
    URL = '{0}/like'.format(BASEURL)
    
    jsondata = simplejson.dumps(testdata)
    h = httplib2.Http()
    resp, content = h.request(URL,
                              'POST',
                              jsondata,
                              headers={'Content-Type': 'application/json'})
    print resp
    print content
    
def testSkip():
    testdata = {"query": {"hard": {"geo":{"x":47,"y":-122,"d":200}, "datetimeRange": {"start":'2010',"end":'2011'}, "budget":{"min":4,"max":5.1}}, "soft":['holy grail']},
                "id":"524c04c4e291973e11364ad4"}
    URL = '{0}/skip'.format(BASEURL)
    
    jsondata = simplejson.dumps(testdata)
    h = httplib2.Http()
    resp, content = h.request(URL,
                              'POST',
                              jsondata,
                              headers={'Content-Type': 'application/json'})
    print resp
    print content


print "Testing recommend"
testRecommend()
print "Testing like"
testLike()
print "Testing skip"
testSkip()