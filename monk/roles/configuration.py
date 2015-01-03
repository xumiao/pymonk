# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 23:42:45 2014

@author: xm
"""
import yaml
import logging
import getopt, os, sys

class Configuration(object):

    def __init__(self, configurationFileName=None, logFileMidName='', pid=''):
        self.uidConnectionString   = 'localhost'
        self.uidDataBaseName       = 'UIDDB'
        
        self.modelConnectionString = 'localhost'
        self.modelDataBaseName     = 'MONKModelTest'
        self.userCollectionName    = 'UserStore'
        self.pandaCollectionName   = 'PandaStore'
        self.turtleCollectionName  = 'TurtleStore'
        self.mantisCollectionName  = 'MantisStore'
        self.tigressCollectionName = 'TigressStore'
        
        self.dataConnectionString  = 'localhost'
        self.dataDataBaseName      = 'MONKDataTest'
        self.entityCollectionName  = 'EntityStore'
        
        self.sysConnectionString   = 'localhost'
        self.sysDataBaseName       = 'MONKSysTest'
        self.engineCollectionName  = 'EngineStore'
        
        self.kafkaConnectionString = 'localhost'
        
        self.workerGroup = 'monkTestWorker'
        self.workerTopic = 'monkTestWorker'
        self.workerConsumerOffsetSkip = -1 #from the end
        self.workerPollInterval = 0.1 #wait 0.1s if no message received
        self.workerExecuteInterval = 0.1 #wait 0.1s if no task to execute
        self.workerMaintainInterval = 60 #1 update per minute
        
        self.administratorGroup = 'monkTestAdmin'
        self.administratorTopic = 'monkTestAdmin'
        self.administratorServerPartitions = [0]
        self.administratorClientPartitions = [1]
        self.administratorOffsetSkip = -1 #from the end
        self.administratorMaxNumWorkers = 32
        self.administratorMaintainInterval = 60 #1 update per minute
        self.administratorPollInterval = 0.1 #wait 0.1s if no message received
        self.administratorExecuteInterval = 0.1 #wait 0.1s if no task to execute
        
        self.monitorGroup = 'monkTestMonitor'
        self.monitorTopic = 'monkTestMonitor'
        self.monitorServerPartitions = [0]
        self.monitorClientPartitions = [1]
        self.monitorOffsetSkip = -1
        self.monitorMaintainInterval = 60
        self.monitorPollInterval = 0.1
        self.monitorExecuteInterval = 0.1
        
        self.brokerTimeout = 200
        
        self.logFileNameStub = 'logs/monk'
        
        if configurationFileName:
            with open(configurationFileName, 'r') as conf:
                self.__dict__.update(yaml.load(conf))
        
        if 'loggingConfig' not in self.__dict__:
            with open('log_config.yml', 'r') as logConf:
                loggingConfig = yaml.load(logConf)
        elif isinstance(self.loggingConfig, str):
            with open(self.loggingConfig, 'r') as logConf:
                loggingConfig = yaml.load(logConf)
        else:
            loggingConfig = self.loggingConfig
            
        if logFileMidName:
            loggingConfig['handlers']['files']['filename'] = \
            '.'.join([self.logFileNameStub, logFileMidName, 'log'])
        
        logging.config.dictConfig(loggingConfig)

DEFAULT_CONFIG_FILE = 'monk_config.yml'

def print_help(helpString):
    print helpString, '-c <configFile>'
    
def get_config(argvs, name, helpString):
    configFile = DEFAULT_CONFIG_FILE
    try:
        opts, args = getopt.getopt(argvs, 'hc:',['configFile='])
    except getopt.GetoptError:
        print_help(helpString)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help(helpString)
            sys.exit()
        elif opt in ('-c', '--configFile'):
            configFile = arg
    return Configuration(configFile, name, str(os.getpid()))
    
