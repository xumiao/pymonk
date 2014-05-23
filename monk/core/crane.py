# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:41 2013
The persistent storage manager that talks to different databases

@author: xm
"""

from pymongo import MongoClient
#TODO: using cache
#from monk.utils.cache import lru_cache
import logging
import base
import constants as cons
from bson.objectid import ObjectId
from uid import UID
logger = logging.getLogger("monk.crane")

class Crane(object):

    def __init__(self, database=None, collectionName=None, fields=None):
        if database is None or collectionName is None:
            return
            
        logger.info('initializing {0} '.format(collectionName))
        self._defaultCollectionName = collectionName
        self._currentCollectionName = collectionName
        self._database = database
        self._coll = self._database[collectionName]
        self._fields = fields        
        self._cache = {}

    # cache related operation
    def __get_one(self, key):
        if key in self._cache:
            return self._cache[key]
        else:
            return None

    def __get_all(self, keys):
        objs = [self._cache[key] for key in keys if key in self._cache]
        rems = [key for key in keys if key not in self._cache]
        return objs, rems

    def __put_one(self, obj):
        self._cache[obj._id] = obj

    def __put_all(self, objs):
        map(self.__put_one, objs)

    def __erase_one(self, obj):
        try:
            del self._cache[obj._id]
        except:
            pass

    def __erase_all(self, objs):
        map(self.__erase_one, objs)

    def set_collection_name(self, collectionName):
        if collectionName:
            self._coll = self._database[collectionName]
            self._currentCollectionName = collectionName
    
    def reset_collection_name(self):
        self._coll = self._database[self._defaultCollectionName]
        self._currentCollectionName = self._defaultCollectionName
    
    def delete_by_id(self, obj):
        if not obj:
            return False
        
        if not isinstance(obj, ObjectId):
            return False
        
        self._coll.remove(obj)
        self.__erase_one(obj)
        return True
        
    def load_or_create(self, obj, tosave=False):
        if obj is None:
            return None
        
        if isinstance(obj, ObjectId):
            return self.load_one_by_id(obj)
        else:
            objId = self.load_one_in_id({'name':obj.get('name', cons.DEFAULT_EMPTY),
                                         'creator':obj.get('creator', cons.DEFAULT_CREATOR)})
            if objId:
                return self.load_one_by_id(objId['_id'])
            elif 'monkType' in obj:
                obj = self.create_one(obj)
                if tosave:
                    obj.save()
                return obj
            else:
                return None

    def load_or_create_all(self, objs, tosave=False):
        if not objs:
            return []
        
        if isinstance(objs[0], ObjectId):
            return self.load_all_by_ids(objs)
        else:
            return [self.load_or_create(obj, tosave) for obj in objs]
    
    def lazy_load(self, field):
        if self._fields is None:
            self._fields = {}
        if True in self._fields.values:
            logger.error('can only be all lazy or explicit')
            logger.debug('original fields {0}'.format(self._fields))
            logger.debug('try to lazy load field {0}'.format(field))
            self._fields = {}
        self._fields[field] = False
    
    def explicit_load(self, field):
        if self._fields is None:
            self._fields = {}
        if False in self._fields.values:
            logger.error('can only be all lazy or explicit')
            logger.debug('original fields {0}'.format(self._fields))
            logger.debug('try to explicitly load field {0}'.format(field))
            self._fields = {}
        self._fields[field] = True
        
    def exists_field(self, obj, field):
        query = {'_id':obj._id, field:{'$exists':True}}
        if self._coll.find_one(query, {'_id':1}):
            return True
        else:
            return False
            
    def exists_fields(self, obj, fields):
        query = {field:{'$exists':True} for field in fields}
        query['_id'] = obj._id
        if self._coll.find_one(query,{'_id':1}):
            return True
        else:
            return False
            
    def remove_field(self, obj, field):
        try:
            self._coll.update({'_id':obj._id}, {'$unset':{field:1}})
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not remove field {0} for obj {1}'.format(field, obj._id))
            return False
        return True

    def remove_fields(self, obj, fields):
        try:
            self._coll.update({'_id':obj._id}, {'$unset':fields})
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not remove fields [{0}] for obj {1}'.format(' , '.join(fields), obj._id))
            return False
        return True
     
    def push_one_in_fields(self, obj, fields):
        try:
            self._coll.update({'_id':obj._id}, {'$push':fields})
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not push document {0} in fields {1}'.format(obj._id, fields))
            return False
        return True
    
    def pull_one_in_fields(self, obj, fields):
        try:
            self._coll.update({'_id':obj._id}, {'$pull':fields})
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not pull fields {0} from document {1}'.format(fields, obj._id))
            return False
        return True
            
    def update_one_in_fields(self, obj, fields):
        # fields are in flat form
        # 'f1.f2':'v' is ok, 'f1.f3' won't be erased
        # 'f1':{'f2':'v'} is NOT, 'f1':{'f3':vv} will be erased
        try:
            self._coll.update({'_id':obj._id}, {'$set':fields}, upsert=True)
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not update document {0} in fields {1}'.format(obj._id, fields))
            return False
        return True
    
    def load_one_in_fields(self, obj, fields):
        # fields is a list
        try:
            return self._coll.find_one({'_id':obj._id}, fields)
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not load document {0} in fields {1}'.format(obj._id, fields))
            return None
    
    def save_one(self, obj):
        obj.save()
    
    def save_all(self, objs):
        [obj.save() for obj in objs]
        
    def create_one(self, obj):
        obj = base.monkFactory.decode(obj)
        if obj:
            self.__put_one(obj)
        return obj
    
    def create_all(self, objs):
        objs = map(base.monkFactory.decode, objs)
        self.__put_all(objs)
        return objs
    
    def load_one_by_id(self, objId):
        obj = self.__get_one(objId)
        if not obj and objId:
            try:
                obj = self._coll.find_one({'_id': objId}, self._fields)
                obj = base.monkFactory.decode(obj)
                if obj:
                    self.__put_one(obj)
            except Exception as e:
                logger.warning(e.message)
                logger.warning('can not load document by id {0}'.format(objId))
                obj = None
        return obj

    def load_all_by_ids(self, objIds):
        objs, rems = self.__get_all(objIds)
        if rems:
            try:
                remainObjs = map(base.monkFactory.decode, 
                                 self._coll.find({'_id': {'$in':rems}}, self._fields))
            except Exception as e:
                logger.warning(e.message)
                logger.warning('can not load remains {0} ...'.format(rems[0]))
                remainObjs = []
            objs.extend(remainObjs)
            self.__put_all(remainObjs)
        return objs

    def load_one_in_id(self, query):
        try:
            return self._coll.find_one(query, {'_id': 1})
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not load document by query'.format(query))
            return None

    def load_all_in_ids(self, query, skip=0, num=0):
        try:
            return list(self._coll.find(query, {'_id': 1}, skip=skip, limit=num))
        except Exception as e:
            logger.warning(e.message)
            logger.warning('can not load documents by query'.format(query))
            return []

    def load_one(self, query, fields):
        try:
            return self._coll.find_one(query, fields)
        except Exception as e:
            logger.warning(e.message)
            logger.warning('query {0} can not be executed'.format(query))
            return None

    def load_all(self, query, fields, skip=0, num=0):
        try:
            return list(self._coll.find(query, fields, skip=skip, limit=num))
        except Exception as e:
            logger.warning(e.message)
            logger.warning('query {0} can not be executed'.format(query))
            return None

    def has_name_user(self, name, user):
        if self._coll.find_one({'name': name, 'creator':user}):
            return True
        else:
            return False

dataClient   = None
dataDB       = None
modelClient  = None
modelDB      = None
uidClient    = None
uidDB        = None
uidStore     = None
entityStore  = Crane()
pandaStore   = Crane()
mantisStore  = Crane()
turtleStore  = Crane()
tigressStore = Crane()

def create_db(connectionString, databaseName):
    try:
        client = MongoClient(connectionString)
        database = client[databaseName]
    except Exception as e:
        logger.warning(e.message)
        logger.warning('failed to connection to database {0}.{1}'.format(connectionString, databaseName))
        return None
    return client, database

def exit_storage():
    global dataClient, modelClient, uidClient
    dataClient.close()
    modelClient.close()
    uidClient.close()
    
def initialize_storage(config):
    global dataClient, modelClient, uidClient
    global dataDB, modelDB, uidDB
    global uidStore, entityStore, pandaStore
    global mantisStore, turtleStore, tigressStore
    
    #initialize uid store
    uidClient, uidDB = create_db(config.uidConnectionString,
                                 config.uidDataBaseName)
    if uidDB is None:
        logger.error('can not access the database {0} at {1}'.format(
                     config.uidDataBaseName,
                     config.uidConnectionString))
        return False
    uidStore = UID(uidDB)

    #initialize data store
    dataClient, dataDB = create_db(config.dataConnectionString,
                                   config.dataDataBaseName)
    if dataDB is None:
        logger.error('can not access the database {0} at {1}'.format(
                     config.dataDataBaseName,
                     config.dataConnectionString))
        return False
    entityStore   = Crane(dataDB,
                          config.entityCollectionName,
                          config.entityFields)

    #initialize model store
    modelClient, modelDB = create_db(config.modelConnectionString,
                                     config.modelDataBaseName)
    if modelDB is None:
        logger.error('can not access the database {0} at {1}'.format(
                     config.modelDataBaseName,
                     config.modelConnectionString))
        return False
    pandaStore   = Crane(modelDB,
                         config.pandaCollectionName,
                         config.pandaFields)
    from panda import Panda
    Panda.store = pandaStore
    mantisStore  = Crane(modelDB,
                         config.mantisCollectionName,
                         config.mantisFields)
    from mantis import Mantis
    Mantis.store = mantisStore
    turtleStore  = Crane(modelDB,
                         config.turtleCollectionName,
                         config.turtleFields)
    from turtle import Turtle
    Turtle.store = turtleStore
    tigressStore = Crane(modelDB,
                         config.tigressCollectionName,
                         config.tigressFields)
    from tigress import Tigress
    Tigress.store = tigressStore
    return True
