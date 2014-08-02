# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 09:09:06 2014
Build a report page to monitor different MONK services
@author: xm
"""
import os
import simplejson
import logging
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from deffered_resource import DefferedResource
from twisted.internet.task import LoopingCall
import traceback

class MonkMetrics(object):
    group = 'metrics'
    bigNumber = 1000000000
    def __init__(self, hosts, timeSpan=1000, timeInterval=10, timeTick=1000, offsetInterval=1000):
        self.kafkaHosts = hosts
        self.timeInterval = timeInterval
        self.timeTick = timeTick
        self.timeSpan = timeSpan
        self.offsetInterval = offsetInterval
        self.maxOffset = 20000
        self.metrics = {}
        self.users = {}
    
    def parseUser(self, user, t, topic, metricName):
        if topic in self.users:
            users = self.users[topic]
        else:
            users = {}
            self.users[topic] = users
            
        if user in users:
            userProfile = users[user]
            userProfile['lastSeen'] = t
            if metricName not in userProfile['metricNames']:
                userProfile['metricNames'].append(metricName)
        else:
            userProfile = {'name':user,
                           'userId':len(users) + 1,
                           'firstSeen':t,
                           'lastSeen':t,
                           'topic':topic,
                           'metricNames':[metricName]}
            users[user] = userProfile
        return userProfile['userId']
        
    def parseMessages(self, topic, messages):
        minTime = self.bigNumber
        maxTime = 0
        if topic in self.metrics:
            metrics = self.metrics[topic]
        else:
            metrics = {}
            self.metrics[topic] = metrics
        for message in reversed(messages):
            body = message.message.value.split(' : ')[1].split(',')
            # user 
            user = body[0].split('=')[1]
            # time
            t = float(body[1].split('=')[1])
            minTime = min(minTime, t)
            maxTime = max(maxTime, t)
            # metric
            name = body[2].split('=')[0]
            value = float(body[2].split('=')[1])
            if name in metrics:
                metric = metrics[name]
            else:
                metric = []
                metrics[name] = metric
            userId = self.parseUser(user, t, topic, name)
            metric.append({'time':t, 'userId':userId, 'value':value})
            print userId, t, value, name, user
        return minTime, maxTime
    
    def normalize_metrics(self):
        for metrics in self.metrics.itervalues():
            for metric in metrics.itervalues():
                metric.sort(key=lambda x:x['time'])
                currtime = metric[-1]['time']
                for m in metric:
                    m['rtime'] = (m['time'] - currtime) / 1000
                    
    def retrieve_metrics(self, topic):
        try:
            kafkaClient = KafkaClient(self.kafkaHosts)
            consumer = SimpleConsumer(kafkaClient, self.group, topic, partitions=[0])
            offset = 0
            timeSpan = 0
            timeNow = 0
            timePast = self.bigNumber
            while offset < self.maxOffset:
                offset += self.offsetInterval
                consumer.seek(-offset, 2)
                messages = consumer.get_messages(count=self.offsetInterval)
                minTime, maxTime = self.parseMessages(topic, messages)
                timeNow = max(maxTime, timeNow)
                timePast = min(minTime, timePast)
                timeSpan = max(timeNow - timePast, timeSpan)
            kafkaClient.close()
            self.normalize_metrics()
        except Exception as e:
            print e
            print traceback.format_exc()

monkMetrics = MonkMetrics('monkkafka.cloudapp.net:9092,monkkafka.cloudapp.net:9093,monkkafka.cloudapp.net:9094')

def monitoring():
    global monkMetrics
    print 'retrieving metrics'
    monkMetrics.retrieve_metrics('exprmetric')
    #monkMetrics.retrieve_metrics('expr2')

#lc = LoopingCall(monitoring)
#lc.start(120)

class Users(DefferedResource):
    isLeaf = True
    def __init__(self, delayTime=0.0):
        DefferedResource.__init__(self, delayTime)
    
    def _get_users(self, args):
        global monkMetrics
        topic = args.get('topic',['exprmetric'])[0]
        metricName = args.get('metricName', ['|dq|/|q|'])[0]
        users = monkMetrics.users.get(topic, {})
        print 'return users for ', topic, metricName
        return [user for user in users.values() if metricName in user['metricNames']]
        
    def _delayedRender_GET(self, request):
        results = self._get_users(request.args)
        simplejson.dump(results, request)
        request.finish()
        
    def _delayedRender_POST(self, request):
        results = self._get_users(request.args)
        simplejson.dump(results, request)
        request.finish()

class  Metrics(DefferedResource):
    isLeaf = True
    def __init__(self, delayTime=0.0):
        DefferedResource.__init__(self, delayTime)
    
    def _get_metrics(self, args):
        global monkMetrics
        topic = args.get('topic', ['exprmetric'])[0]
        metricName = args.get('metricName', ['|dq|/|q|'])[0]
        monkMetrics.retrieve_metrics(topic)
        metrics = monkMetrics.metrics.get(topic, {}).get(metricName, [])
        print 'return metrics for ', topic, metricName
        return metrics
        
    def _delayedRender_GET(self, request):
        results = self._get_metrics(request.args)
        simplejson.dump(results, request)
        request.finish()
        
    def _delayedRender_POST(self, request):
        results = self._get_metrics(request.args)
        simplejson.dump(results, request)
        request.finish()
    
root = DefferedResource()
indexpage = File('./web/')
root.putChild("monitor", indexpage)
root.putChild("users", Users())
root.putChild("metrics", Metrics())

site = Site(root, "monkmonitor.log")
reactor.listenTCP(80, site)
reactor.run()
