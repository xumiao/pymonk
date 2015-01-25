# -*- coding: utf-8 -*-
"""
Created on Fri Dec 12 07:01:01 2014

@author: xm
"""

import monk.core.api as monkapi
from Queue import PriorityQueue
import time
import logging
import platform
if platform.system() == 'Windows':
    import win32api
else:
    import signal
import tornado.httpserver
import tornado.ioloop
import tornado.web 
import simplejson
import traceback

logger = logging.getLogger('monk.network.server')

now = time.time

class TaskFactory(object):
    def __init__(self):
        self.factory = {}

    def register(self, TaskClass):
        className = TaskClass.__name__
        if className not in self.factory:
            logger.debug('className {} is registering'.format(className))
            self.factory[TaskClass.__name__] = TaskClass
 
    def find(self, name):
        return [key for key in self.factory.iterkeys() if key.find(name) >= 0]
        
    def create(self, message):
        try:
            generic = simplejson.loads(message)
            name = generic.get('op', None)
            if not name:
                logger.warning('no task defined in op')
                return None
            else:
                return self.factory[name](generic)
        except Exception as e:
            logger.debug('can not create tasks for {}'.format(message))
            logger.debug('Exception {}'.format(e))
            logger.debug(traceback.format_exc())
            return None

taskFactory = TaskFactory()

class Task(object):
    PRIORITY_HIGH = 1
    PRIORITY_LOW = 5
    FPRIORITY = 'priority'
    
    def __init__(self, decodedMessage):
        self.decodedMessage = decodedMessage
        self.priority = int(decodedMessage.get(Task.FPRIORITY, Task.PRIORITY_LOW))
        self.name = self.decodedMessage.get('name')
        if self.name and isinstance(self.name, list):
            self.name = tuple(self.name)
        self.turtleName = self.decodedMessage.get('turtleName')
        self.userName = self.name
    
    def info(self, logger, message):
        logger.info('{} for {}'.format(message, self.decodedMessage))
    
    def warning(self, logger, message):
        logger.warning('{} for {}'.format(message, self.decodedMessage))
    
    def error(self, logger, message):
        logger.error('{} for {}'.format(message, self.decodedMessage))
        
    def get(self, name, defaultValue=None):
        return self.decodedMessage.get(name, defaultValue)
        
    def act(self):
        self.warning(logger, 'no task is defined')

def taskT(TaskClass):
    taskFactory.register(TaskClass)
    
class Echo(Task):
    def act(self):
        logger.info('received message {}'.format(self.decodedMessage))
taskT(Echo)
        
class MonkServer(object):    
    EXIT_WAIT_TIME=3
    MAX_QUEUE_SIZE=100000
    MAINTAIN_INTERVAL=10000
    POLL_INTERVAL=0.1
    EXECUTE_INTERVAL=0.1
    
    def __init__(self, serverName='', config=None):
        if not config:
            self.ready = False
            return
        self.pq = PriorityQueue(self.MAX_QUEUE_SIZE)
        self.serverName = serverName
        self.lastMaintenance = now()
        self.ioLoop = tornado.ioloop.IOLoop.instance()        
        self.httpServer = None
        self.port = 8888
        self.webApps = []
        self.brokers = self.init_brokers(config)
        if platform.system() == 'Windows':
            win32api.SetConsoleCtrlHandler(self._sig_handler, 1)
        else:
            signal.signal(signal.SIGINT,  self._sig_handler)
            signal.signal(signal.SIGTERM, self._sig_handler)
        self.ready = True
        
    def _sig_handler(self, sig, frame):
        logger.warning('Caught signal : {}'.format(sig))
        self.ioLoop.add_callback(self._onexit)
        
    def _onexit(self):
        logger.info('stopping the server {}'.format(self.serverName))
        if self.httpServer:
            self.httpServer.stop()
        logger.info('exit in {} seconds'.format(self.EXIT_WAIT_TIME))
        
        #deadline = now() + self.EXIT_WAIT_TIME
        logger.info('onexit')
        self.onexit()
        
        logger.info('stopping ioloop')
        self.ioLoop.stop()
        for broker in self.brokers:
            logger.info('closing broker {}'.format(broker))
            broker.close()
        logger.info('stopping monkapi')
        monkapi.exits()
        #def stop_loop():
        #    logger.info('stopping loop')
        #    nowt = now()
        #    if nowt < deadline and (self.ioLoop._callbacks or self.ioLoop._timeouts):
        #        self.ioLoop.add_timeout(nowt + 1, stop_loop)
        #    else:
        #        self.ioLoop.stop()
        #        for broker in self.brokers:
        #            logger.info('closing broker')
        #            broker.close()
        #        logger.info('exiting monkapi')
        #        monkapi.exits()
        #stop_loop()
        logger.info('exited')
        
    def _maintain(self):
        self.maintain()
        self.ioLoop.add_timeout(now() + self.MAINTAIN_INTERVAL, self._maintain)

    def _poll(self):
        if self.pq.full():
            logger.debug('queue is full')
            self.ioLoop.add_timeout(now() + self.POLL_INTERVAL, self._poll)
        else:
            ready = filter(None, (broker.is_consumer_ready() for broker in self.brokers))
            if not ready:
                self._onexit()
                return
            taskScripts = filter(None, (broker.consume_one() for broker in self.brokers))
            for tscript in taskScripts:
                t = taskFactory.create(tscript)
                if t:
                    self.pq.put((t.priority, t), block=False)
            if taskScripts:
                #logger.debug('processing next task')
                self.ioLoop.add_callback(self._poll)
            else:
                #logger.debug('waiting on the polling')
                self.ioLoop.add_timeout(now() + self.POLL_INTERVAL, self._poll)
    
    def _execute(self):
        if self.pq.queue:
            try:
                priority, task = self.pq.get()
                task.act()
                logger.debug('executing {}'.format(task.name))
            except Exception as e:
                logger.debug(e.message)
                logger.debug(traceback.format_exc())
            finally:
                self.ioLoop.add_callback(self._execute)
        else:
            logger.debug('waiting for tasks {}'.format(now()))
            self.ioLoop.add_timeout(now() + self.EXECUTE_INTERVAL, self._execute)

    def add_application(self, regx, handler):
        self.webApps.append((regx, handler))
            
    def init_brokers(self, argvs):
        raise Exception('not implemented yet')
    
    def maintain(self):
        pass
    
    def onexit(self):
        pass

    def run(self):
        if not self.ready:
            logger.info('server {} is not intialized properly'.format(self.serverName))
            return
            
        self.ioLoop.add_timeout(now() + self.MAINTAIN_INTERVAL, self._maintain)
        self.ioLoop.add_timeout(now() + self.POLL_INTERVAL, self._poll)
        self.ioLoop.add_timeout(now() + self.EXECUTE_INTERVAL, self._execute)
        
        if self.webApps:
            # fail immediately if http server can not run
            application = tornado.web.Application(self.webApps)
            self.httpServer = tornado.httpserver.HTTPServer(application)
            self.httpServer.listen(self.port)
        
        logger.info('{} is running'.format(self.serverName))        
        self.ioLoop.start()        
        logger.info('{} is exiting'.format(self.serverName))
