# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:51:41 2013
The persistent storage manager that talks to different databases

@author: xm
"""

import pymongo as pm
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
    def _getOne(self, key):
        if key in self._cache:
            return self._cache[key]
        else:
            return None

    def _getAll(self, keys):
        objs = [self._cache[key] for key in keys if key in self._cache]
        rems = [key for key in keys if key not in self._cache]
        return objs, rems

    def _putOne(self, obj):
        if obj:
            self._cache[obj._id] = obj

    def _putAll(self, objs):
        map(self._putOne, objs)

    def _eraseOne(self, obj):
        if obj._id in self._cache:
            del self._cache[obj._id]

    def _eraseAll(self, objs):
        map(self._eraseOne, objs)

    def _clear(self):
        self._cache.clear()

    # database related operation
    def alive(self):
        return self._conn and self._conn.alive()

    def saveOne(self, obj):
        if self._coll:
            self._coll.save(obj)
            self._putOne(obj)

    def saveAll(self, objs):
        if self._coll and objs:
            map(self._coll.save, objs)
            self._putAll(objs)

    def loadOneById(self, objId):
        obj = self._getOne(objId)
        if not obj:
            try:
                obj = self._coll.find_one({'_id': objId}, self._fields)
                self._putOne(obj)
            except Exception as e:
                logging.warning('exception {0}'.format(e.message))
                obj = None
        return obj

    def loadAllByIds(self, objIds):
        objs, rems = self._getAll(objIds)
        if rems and self._coll:
            try:
                remainObjs = self._coll.find(
                    {'_id': {'$in', rems}}, self._fields)
            except:
                remainObjs = []
            objs.extend(remainObjs)
            self._putAll(remainObjs)
        return objs

    def loadOneInId(self, query):
        try:
            return self._coll.find_one(query, {'_id': 1})
        except Exception as e:
            logging.warning('exception {0}'.format(e.message))
            return None

    def loadAllInIds(self, query):
        if query and self._coll:
            return self._coll.find(query, {'_id': 1})
        else:
            return []

    def loadOne(self, query, fields):
        if query and self._coll:
            return self._coll.find_one(query, fields)
        else:
            return None

    def loadAll(self, query, fields):
        if query and self._coll:
            return self._coll.find(query, fields)
        else:
            return []

    def hasName(self, name):
        if self._coll.find_one({'name': name}):
            return True
        else:
            return False
