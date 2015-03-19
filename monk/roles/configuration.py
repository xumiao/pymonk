# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 23:42:45 2014

@author: xm
"""
import yaml
import logging
import logging.config
import getopt, os, sys
logger = logging.getLogger('monk.roles.configuration')

class Configuration(object):

    def __init__(self, configurationFileName=None, logFileDir='.', roleName='', pid=''):
        self.mongoConnectionString = 'localhost'
        self.uidDataBaseName       = 'UIDDB'
        
        self.modelDataBaseName     = 'MONKModelTest'
        self.userCollectionName    = 'UserStore'
        self.pandaCollectionName   = 'PandaStore'
        self.turtleCollectionName  = 'TurtleStore'
        self.mantisCollectionName  = 'MantisStore'
        self.tigressCollectionName = 'TigressStore'
        
        self.dataDataBaseName      = 'MONKDataTest'
        self.entityCollectionName  = 'EntityStore'
        
        self.sysDataBaseName       = 'MONKSysTest'
        self.engineCollectionName  = 'EngineStore'
        
        self.kafkaConnectionString = 'localhost'
        
        self.workerGroup = 'monkTestWorker'
        self.workerTopic = 'monkTestWorker'
        self.workerConsumerOffsetSkip = -1 #from the end
        self.workerMaxQueueSize = 100000
        self.workerPollInterval = 0.1 #wait 0.1s if no message received
        self.workerExecuteInterval = 0.1 #wait 0.1s if no task to execute
        self.workerMaintainInterval = 60 #1 update per minute
        
        self.administratorGroup = 'monkTestAdmin'
        self.administratorTopic = 'monkTestAdmin'
        self.administratorServerPartitions = [0]
        self.administratorClientPartitions = [1]
        self.administratorOffsetSkip = -1 #from the end
        self.administratorMaxNumWorkers = 32
        self.administratorMaxQueueSize = 100000
        self.administratorMaintainInterval = 60 #1 update per minute
        self.administratorPollInterval = 0.1 #wait 0.1s if no message received
        self.administratorExecuteInterval = 0.1 #wait 0.1s if no task to execute
        
        self.monitorGroup = 'monkTestMonitor'
        self.monitorTopic = 'monkTestMonitor'
        self.monitorServerPartitions = [0]
        self.monitorOffsetSkip = -1
        self.monitorMaxQueueSize = 100000
        self.monitorMaintainInterval = 60
        self.monitorPollInterval = 0.1
        self.monitorExecuteInterval = 0.1
        
        self.brokerTimeout = 200
        
        self.roleName = roleName
        self.logFileDir = logFileDir
        if configurationFileName:
            with open(configurationFileName, 'r') as conf:
                self.__dict__.update(yaml.load(conf))
                
        if 'modelConnectionString' not in self.__dict__:
            self.modelConnectionString = self.mongoConnectionString
        if 'uidConnectionString' not in self.__dict__:
            self.uidConnectionString = self.mongoConnectionString
        if 'dataConnectionString' not in self.__dict__:
            self.dataConnectionString = self.mongoConnectionString
        if 'sysConnectionString' not in self.__dict__:
            self.sysConnectionString = self.mongoConnectionString
                        
        if 'loggingConfig' not in self.__dict__:
            self.loggingConfig = 'log_config.yml'
        
        config_logging(self.loggingConfig, self.roleName, self.logFileDir)
        
def config_logging(loggingConfig, logFileMidName='test', logFileDir='.'):
        if isinstance(loggingConfig, str):
            with open(loggingConfig, 'r') as logConf:
                loggingConfig = yaml.load(logConf)
        
        loggingConfig['handlers']['files']['filename'] = \
        '{}/monk.{}.log'.format(logFileDir, logFileMidName)
        
        logging.config.dictConfig(loggingConfig)
        logger.info('configuration done')
    
DEFAULT_CONFIG_FILE = 'monk_config.yml'
DEFAULT_LOG_FILE_DIR = '.'

def print_help(helpString):
    print helpString, '-c <configFile> -l <logFileDir>'

def default_config():
    return Configuration(DEFAULT_CONFIG_FILE, DEFAULT_LOG_FILE_DIR, 'console', str(os.getpid()))
    
def get_config(argvs, name, helpString):
    configFile = DEFAULT_CONFIG_FILE
    logFileDir = DEFAULT_LOG_FILE_DIR
    try:
        opts, args = getopt.getopt(argvs, 'hc:l:',['configFile=','logFileDir'])
    except getopt.GetoptError:
        print_help(helpString)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help(helpString)
            sys.exit()
        elif opt in ('-c', '--configFile'):
            configFile = arg
        elif opt in ('-l', '--logFileDir'):
            logFileDir = arg
    return Configuration(configFile, logFileDir, name, str(os.getpid()))
    
