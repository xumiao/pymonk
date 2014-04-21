# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 08:19:09 2013

@author: xm
"""
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor

class DefferedResource(Resource):
    def __init__(self, delayTime = 0.0):
        Resource.__init__(self)
        self.delayTime = delayTime

    def render_GET(self, request):
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours        
        reactor.callLater(self.delayTime, self._delayedRender_GET, request)
        return NOT_DONE_YET
    
    def render_POST(self, request):
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'POST')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours        
        reactor.callLater(self.delayTime, self._delayedRender_POST, request)
        return NOT_DONE_YET
                