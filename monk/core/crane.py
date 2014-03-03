# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:41 2013
The persistent storage manager that talks to different databases

@author: xm
"""

import pymongo as pm
#@todo: using cache
#from monk.utils.cache import lru_cache
import logging


class Crane(object):

    def __init__(self, connectionString,
                 databaseName,
                 collectionName,
                 fields,
                 transformer):
        self._connectionString = connectionString
        self._databaseName = databaseName
        self._collectionName = collectionName
        self._conn = pm.Connection(connectionString)
        self._database = self._conn[self._databaseName]
        self._database.add_son_manipulator(transformer)
        self._coll = self._database[self._collectionName]
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
        del self._cache[obj._id]

    def __erase_all(self, objs):
        map(self.__erase_one, objs)

    # database related operation
    def alive(self):
        return self._conn and self._conn.alive()

    def insert_one(self, obj):
        try:
            if self._coll.find_one({'_id':obj._id}):
                logging.warning('Object {0} already exists'.format(obj.generic()))
                logging.warning('Use updating instead')
                return
            self._coll.save(obj)
            self.__put_one(obj)
        except Exception as e:
            logging.warning(e.message)
            logging.warning('can not save document {0}'.format(obj.generic()))
    
    def update_one_in_fields(self, obj, fields):
        try:
            self._coll.update({'_id':obj._id}, {'$set':fields}, upsert=False)
        except Exception as e:
            logging.warning(e.message)
            logging.warning('can not update document {0} in fields {1}'.format(obj._id, fields))
    
    def load_one_in_fields(self, obj, fields):
        # fields is a list
        try:
            return self._coll.find_one({'_id':obj._id}, fields)
        except Exception as e:
            logging.warning(e.message)
            logging.warning('can not load document {0} in fields {1}'.format(obj._id, fields))
            return None
            
    def load_one_by_id(self, objId):
        obj = self.__get_one(objId)
        if not obj:
            try:
                obj = self._coll.find_one({'_id': objId}, self._fields)
                self.__put_one(obj)
            except Exception as e:
                logging.warning(e.message)
                logging.warning('can not load document by id {0}'.format(objId))
                obj = None
        return obj

    def load_all_by_ids(self, objIds):
        objs, rems = self.__get_all(objIds)
        if rems:
            try:    
                remainObjs = self._coll.find(
                    {'_id': {'$in', rems}}, self._fields)
            except Exception as e:
                logging.warning(e.message)
                logging.warning('can not load remains {0} ...'.format(rems[0]))
                remainObjs = []
            objs.extend(remainObjs)
            self.__put_all(remainObjs)
        return objs

    def load_one_in_id(self, query):
        try:
            return self._coll.find_one(query, {'_id': 1})
        except Exception as e:
            logging.warning(e.message)
            logging.warning('can not load document by query'.format(query))
            return None

    def load_all_in_ids(self, query):
        try:
            return self._coll.find(query, {'_id': 1})
        except Exception as e:
            logging.warning(e.message)
            logging.warning('can not load documents by query'.format(query))
            return []

    def load_one(self, query, fields):
        try:
            return self._coll.find_one(query, fields)
        except Exception as e:
            logging.warning(e.message)
            logging.warning('query {0} can not be executed'.format(query))
            return None

    def load_all(self, query, fields):
        try:
            return self._coll.find(query, fields)
        except Exception as e:
            logging.warning(e.message)
            logging.warning('query {0} can not be executed'.format(query))
            return None

    def has_name(self, name):
        if self._coll.find_one({'name': name}):
            return True
        else:
            return False
