# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 15:02:18 2013
Generate UID from a database
@author: xm
"""
import pymongo as pm


class UID:
    uidChunk = 1024L
    uidCollectionName = 'UIDStore'

    def __init__(self, connectionString, databaseName):
        self.__conn = pm.Connection(connectionString)
        self.__db = self.__conn[databaseName]
        self.__coll = self.__db[self.uidCollectionName]
        self.__pivotUid = 0L
        self.__currentUid = 0L
        self.__nextChunk()

    def __nextChunk(self):
        doc = self.__coll.find_and_modify({}, {'$inc': {'Uid': self.uidChunk}})
        if not doc:
            self.__currentUid = 0L
            self.__coll.save({'Uid': self.uidChunk})
        else:
            self.__currentUid = long(doc['Uid'])
        self.__pivotUid = self.__currentUid + self.uidChunk

    def nextUID(self):
        if self.__currentUid >= self.__pivotUid:
            self.__nextChunk()
        self.__currentUid += 1L
        return self.__currentUid
