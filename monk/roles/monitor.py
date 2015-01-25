# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 09:09:06 2014
Build a report page to monitor different MONK services
@author: xm
"""
from monk.roles.configuration import get_config
import monk.core.api as monkapi
import logging
from monk.network.broker import KafkaBroker
from monk.network.server import taskT, Task, MonkServer
import sys
import time
from collections import deque
from tornado.web import RequestHandler
from bokeh.resources import INLINE
from bokeh.plotting import figure, file_html, decode_utf8
import numpy as np

logger = logging.getLogger('monk.roles.monitor')

DEFAULT_MONITOR_USER='_monitor_'

class MonitorBroker(KafkaBroker):
    def track(self, name, value, user=DEFAULT_MONITOR_USER):
        self.produce('Track', name, user=user, value=value, time=time.time())
    
    def aggregate(self, name, value, user=DEFAULT_MONITOR_USER):
        self.produce('Aggregate', name, user=user, value=value)

    def measure(self, name, value, label=1, user=DEFAULT_MONITOR_USER):
        self.produce('Measure', name, user=user, value=value, label=label)
        
    def reset_tracker(self, name):
        self.produce('ResetTracker', name)
    
    def reset_aggregator(self, name):
        self.produce('ResetAggregator', name)
    
    def reset_measurer(self, name):
        self.produce('ResetMeasurer', name)
        
    def rename_tracker(self, name, newname):
        self.produce('RenameTracker', name, newname=newname)
    
    def rename_aggregator(self, name, newname):
        self.produce('RenameAggregator', name, newname=newname)
    
    def rename_measurer(self, name, newname):
        self.produce('RenameMeasurer', name, newname=newname)
    
    def annotate_tracker(self, name, annotator):
        self.produce('AnnotateTracker', name, annotator=annotator, time=time.time())

class MonkMonitor(MonkServer):
    def init_brokers(self, config):
        self.trackers = {}
        self.aggregators = {}
        self.measurers = {}
        monkapi.initialize(config)
        self.MAINTAIN_INTERVAL = config.monitorMaintainInterval
        self.POLL_INTERVAL = config.monitorPollInterval
        self.EXECUTE_INTERVAL = config.monitorExecuteInterval
        self.MAX_QUEUE_SIZE = config.monitorMaxQueueSize
        self.monitorBroker = MonitorBroker(config.kafkaConnectionString,
                                           config.monitorGroup,
                                           config.monitorTopic, 
                                           KafkaBroker.SIMPLE_CONSUMER)
        return [self.monitorBroker]

monitor = MonkMonitor()

class Tracker(object):    
    def __init__(self, retireTime=7200, resolution=1):
        self.valuesTimed = dict()
        self.numTimed = dict()
        self.annotatorTimed = dict()
        self.queue = deque()
        self.resolution = resolution
        self.retiredTime = int(retireTime / resolution)
        
    def add(self, t, value, user):
        t = int(t / self.resolution)
        firstTime = self.queue[0]
        if t - firstTime > self.retiredTime:
            if firstTime in self.valuesTimed:
                del self.valuesTimed[firstTime]
                del self.numTimed[firstTime]
                del self.annotatorTimed[firstTime]
            self.queue.popleft()
        self.queue.append(t)
        if t in self.valuesTimed:
            if user in self.valuesTimed:
                self.valuesTimed[t][user] += value
                self.numTimed[t][user] += 1.0
            else:
                self.valuesTimed[t][user] = value
                self.numTimed[t][user] = 1.0
        else:
            self.valuesTimed[t] = {user:value}
            self.numTimed[t] = {user:1.0}
    
    def annotate(self, t, annotator):
        t = int(t / self.resolution)
        if t in self.annotatorTimed:
            logger.warning('another annotator {} already at time {}'.format(\
                self.annotatorTimed[t], t * self.resolution))
        else:
            self.annotatorTimed[t] = annotator
            
    def clear(self):
        self.queue.clear()
        self.valuesTimed.clear()
        self.numTimed.clear()
        
class Track(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid tracking name set')
            return
        try:
            value = float(self.get('value'))
        except:
            self.warning(logger, 'no valid value set')
            return
        try:
            t = float(self.get('time'))
        except:
            self.warning(logger, 'no valid time set')
            return
        user = self.get('user')
        if key not in monitor.trackers:
            monitor.trackers[key] = Tracker()
        tracker = monitor.trackers[key]
        tracker.add(t, value, user)
taskT(Track)
        
class ResetTracker(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid tracking name set')
            return
        if key in monitor.trackers:
            monitor.trackers[key].clear()
taskT(ResetTracker)

class RenameTracker(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid tracking name set')
            return
        newname = self.get('newname')
        if key in monitor.trackers and newname:
            monitor.trackers[newname] = monitor.trackers[key]
            del monitor.trackers[key]
taskT(RenameTracker)

class AnnotateTracker(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid tracking name set')
            return
        annotator = self.get('annotator')
        try:
            t = float(self.get('time'))
        except:
            self.warning(logger, 'no valid time set')
            return
        if annotator and key in monitor.trackers:
            tracker = monitor.trackers[key]
            tracker.annotate(t, annotator)
taskT(AnnotateTracker)
            
class Aggregator(object):
    def __init__(self, resolution=0.01):
        self.resolution = resolution
        self.hist = dict()
        self.num = dict()
    
    def clear(self):
        self.hist.clear()
        self.num.clear()
    
    def add(self, value, user):
        vL = int(value / self.resolution)
        vH = vL + 1
        wL = value / self.resolution - vL
        wH = 1.0 - wL
        if user in self.hist:
            hist = self.hist[user]
            if vL in hist:
                hist[vL] += wL
            else:
                hist[vL] = wL
            if vH in hist:
                hist[vH] += wH
            else:
                hist[vH] = wH
            self.num[user] += 1.0
        else:
            self.hist[user] = {vL:wL, vH:wH}
            self.num[user] = 1.0
        
class Aggregate(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid aggregator name set')
            return
        try:
            value = float(self.get('value'))
        except:
            self.warning(logger, 'no valid value set')
            return
        user = self.get('user')
        if key not in monitor.aggregators:
            monitor.aggregators[key] = Aggregator()
        aggregator = monitor.aggregators[key]
        aggregator.add(value, user)
taskT(Aggregate)

class ResetAggregator(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid aggregator name set')
            return
        if key in monitor.aggregators:
            monitor.aggregators[key].clear()
taskT(ResetAggregator)

class RenameAggregator(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid aggregator name set')
            return
        newname = self.get('newname')
        if key in monitor.aggregators and newname:
            monitor.aggregators[newname] = monitor.aggregators[key]
            del monitor.aggregators[key]
taskT(RenameAggregator)

class Measurer(object):
    def __init__(self, resolution=0.01):
        self.resolution = resolution
        self.scores = dict()
        self.totalPos = dict()
        self.totalNeg = dict()
        self.PRCs = None
        self.ROCs = None
        self.invalid = True
        
    def clear(self):
        self.scores.clear()
        self.totalPos.clear()
        self.totalNeg.clear()
        self.PRCs = None
        self.ROCs = None
        self.invalid = True
    
    def add(self, value, user, label):
        if user not in self.scores:
           self.scores[user] = []
           self.totalNeg[user] = 0
           self.totalPos[user] = 0
        self.scores[user].append((value, label))
        if label > 0:
            self.totalPos[user] += 1
        else:
            self.totalNeg[user] += 1
        self.invalid = True
    
    def intervals(self):
        num = int(1.0 /self.resolution) + 1
        return np.linspace(0.0, 1.0, num)
        
    def compute_metrics(self):
        # the number of buckets for the curves
        num = int(1.0 /self.resolution) + 1
        logger.debug('num = {}'.format(num))
        self.PRCs = None
        self.ROCs = None
        PRCn = np.zeros(num, dtype=int)
        ROCn = np.zeros(num, dtype=int)
        for user in self.scores:
            if user is DEFAULT_MONITOR_USER:
                continue
            # initialize basic metrics
            tp = self.totalPos[user]
            tn = 0
            fp = self.totalNeg[user]
            fn = 0
            totalP = tp
            totalN = fp
            logger.debug('totalP={}, totalN={}'.format(totalP, totalN))
            # ignore incomplete user
            if totalP == 0 or totalN == 0:
                continue
            # sort the scores
            score = self.scores[user]
            logger.info('scores for {} : {}'.format(score, user))
            score.sort()
            logger.info('scores for {} : {}'.format(score, user))
            # initialize PRC and ROC
            PRC = np.zeros(num)
            ROC = np.zeros(num)
            PRCn.fill(0)
            ROCn.fill(0)
            # loop through scores
            for s, label in score:
                if label > 0: # positive example
                    fn += 1
                    tp -= 1
                else:   # negative example
                    tn += 1
                    fp -= 1
                recall = float(tp) / float(totalP)
                # precision value
                if tp + fp == 0:
                    precision = 1
                else:
                    precision = float(tp) / float(tp + fp)
                v = int(precision / self.resolution)
                PRC[v] += recall
                PRCn[v] += 1
                # false positive rate value
                fpr = float(fp) / float(totalN)
                v = int(fpr / self.resolution)
                ROC[v] += recall
                ROCn[v] += 1
            logger.info('PRC {}'.format(PRC))
            logger.info('PRCn {}'.format(PRCn))
            logger.info('ROC {}'.format(ROC))
            logger.info('ROCn {}'.format(ROCn))
            
            # averaging ROC and PRC since multiple recalls might fall into the same bucket
            # fill the missing buckets
            for v in reversed(range(num-1)):
                if PRCn[v] == 0:
                    # fill the missing values from high precision
                    # precision == 1 is assumed to exist all the time
                    PRC[v] = PRC[v+1]
                else:
                    # average over all recalls at this precision
                    PRC[v] /= PRCn[v]
            for v in range(2,num):
                if ROCn[v] == 0:
                    # fill the missing values from low fpr
                    # fpr == 0 is assumed to exist all the time
                    ROC[v] = ROC[v-1]
                else:
                    # average over all recalls at this fpr
                    ROC[v] /= ROCn[v]
            if self.ROCs is None:
                self.ROCs = ROC
            else:
                self.ROCs = np.vstack((self.ROCs, ROC))
            if self.PRCs is None:
                self.PRCs = PRC
            else:
                self.PRCs = np.vstack((self.PRCs, PRC))
        self.ROCs.sort(axis=0)
        self.PRCs.sort(axis=0)
        logger.info('ROCs {}'.format(self.ROCs))
        logger.info('PRCs {}'.format(self.PRCs))
        self.invalid = False

    def set_resolution(self, resolution):
        try:
            self.resolution = float(resolution)
            self.invalid = True
        except:
            logger.warning('resolution can not be converted to a float {}'.format(resolution))
        
    def get_ROCs(self):
        if self.invalid:
            self.compute_metrics()
        return self.ROCs
    
    def get_PRCs(self):
        if self.invalid:
            self.compute_metrics()
        return self.PRCs
        
class Measure(Task):
    def act(self):
        logger.info('measure {}'.format(self.decodedMessage))
        key = self.name
        if not key:
            self.warning(logger, 'no valid measurer name set')
            return
        try:
            value = float(self.get('value'))
        except:
            self.warning(logger, 'no valid value set')
            return
        try:
            pos = int(self.get('label'))
        except:
            self.warning(logger, 'no valid label')
            return
        user = self.get('user')
        if key not in monitor.measurers:
            monitor.measurers[key] = Measurer()
        measurer = monitor.measurers[key]
        measurer.add(value, user, pos)
taskT(Measure)

class ResetMeasurer(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid measurer name set')
            return
        if key in monitor.measurers:
            monitor.measurers[key].clear()
taskT(ResetMeasurer)

class RenameMeasurer(Task):
    def act(self):
        key = self.name
        if not key:
            self.warning(logger, 'no valid measurer name set')
            return
        newname = self.get('newname')
        if key in monitor.measurers and newname:
            monitor.measurers[newname] = monitor.measurers[key]
            del monitor.measurers[key]
taskT(RenameMeasurer)

# TODO: TrackerHandler
# TODO: AggregatorHandler
            
class AccuracyHandler(RequestHandler):
    def draw(self, p, accuracies, intervals, resolution, fillColor):
        if accuracies is not None:
            m = accuracies.shape[0]
            logger.debug('m = {}'.format(m))
            maxs   = accuracies[-1]
            mins   = accuracies[0]
            uppers = accuracies[-(1 + m/4)]
            lowers = accuracies[m/4]
            logger.debug('maxs = {}'.format(maxs))
            logger.debug('mins = {}'.format(mins))
            logger.debug('uppers = {}'.format(uppers))
            logger.debug('lowers = {}'.format(lowers))
            p.segment(intervals, maxs, intervals, mins, color='black', toolbar_location='left')
            p.rect(intervals, (uppers + lowers) / 2, resolution / 2, \
                   abs(uppers - lowers), fill_color=fillColor, line_color='black')
        
    def get(self):
        name = self.get_argument('name', None)
        fillColor = self.get_argument('fillColor', "#F2583E")
        resolution = self.get_argument('resolution', None)
        accType = self.get_argument('accType', 'ROC')
        logger.info('request {} {} {}'.format(name, fillColor, resolution))
        if name and name in monitor.measurers:
            measurer = monitor.measurers[name]
            logger.debug('set resolution {}'.format(resolution))
            measurer.set_resolution(resolution)
            if accType == 'ROC':
                accuracies = measurer.get_ROCs()
            elif accType == 'PRC':
                accuracies = measurer.get_PRCs()
            else:
                accuracies = None
            intervals = measurer.intervals()
            resolution = measurer.resolution
        else:
            accuracies = None
            intervals = None
            resolution = 0.01
        logger.debug('accuracies {}'.format(accuracies))
        logger.debug('intervals {}'.format(intervals))
        logger.debug('resolution {}'.format(resolution))
        TOOLS = 'pan,wheel_zoom,box_zoom,reset,save'
        p = figure(tools=TOOLS, plot_width=1000)
        self.draw(p, accuracies, intervals, resolution, fillColor)
        p.title = '{} for {}'.format(accType, name)
        p.grid.grid_line_alpha = 0.3
        response = file_html(p, INLINE, p.title)
        self.write(decode_utf8(response))
        self.set_header("Content-Type", "text/html")
        

def main():
    global monitor
    myname = 'monitor'
    config = get_config(sys.argv[1:], myname, 'monkmonitor.py')
    monitor = MonkMonitor(myname, config)
    monitor.add_application(r'/accuracy', AccuracyHandler)
    monitor.run()

if __name__=='__main__':
    main()
