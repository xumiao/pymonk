# -*- coding: utf-8 -*-
"""
Created on Sun Mar 02 12:29:03 2014

@author: pacif_000
"""
from monk.core.monk import *
from monk.core.uid import UID
from monk.core.crane import *
import os

#@todo: change to scan paths
#@todo: change to yml file for configuration
config = Configuration(os.getenv('MONK_CONFIG_FILE', 'monk.config'))

logging.basicConfig(format='[%(asctime)s]#[%(levelname)s] : %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=eval(config.logLevel))

logging.info('initializing uid store')
uidStore = UID(config.modelConnectionString,
               config.modelDataBaseName)

logging.info('initializing entity store')
entityStore = Crane(config.dataConnectionString,
                    config.dataDataBaseName,
                    config.entityCollectionName,
                    eval(config.entityFields))
logging.info('finished entity store')
logging.info('initializing relation store')
relationStore = Crane(config.dataConnectionString,
                      config.dataDataBaseName,
                      config.relationCollectionName,
                      eval(config.relationFields))
logging.info('finished relation store')
logging.info('initializing panda store')
pandaStore = Crane(config.modelConnectionString,
                   config.modelDataBaseName,
                   config.pandaCollectionName,
                   eval(config.pandaFields))
logging.info('finished panda store')
logging.info('initializing mantis store')
mantisStore = Crane(config.modelConnectionString,
                    config.modelDataBaseName,
                    config.mantisCollectionName,
                    eval(config.mantisFields))
logging.info('finished mantis store')
logging.info('initializing turtle store')
turtleStore = Crane(config.modelConnectionString,
                    config.modelDataBaseName,
                    config.turtleCollectionName,
                    eval(config.turtleFields))
logging.info('finished turtle store')
logging.info('initializing monkey store')
monkeyStore = Crane(config.modelConnectionString,
                    config.modelDataBaseName,
                    config.monkeyCollectionName,
                    eval(config.monkeyFields))
logging.info('finished monkey store')
logging.info('initializing tigress store')
tigressStore = Crane(config.modelConnectionString,
                     config.modelDataBaseName,
                     config.tigressCollectionName,
                     eval(config.tigressFields))
logging.info('finished tigress store')
logging.info('initializing viper store')
viperStore = Crane(config.modelConnectionString,
                   config.modelDataBaseName,
                   config.viperCollectionName,
                   eval(config.viperFields))
logging.info('finished viper store')

