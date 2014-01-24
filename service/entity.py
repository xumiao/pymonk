# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 11:23:54 2013

@author: xumiao
"""

from twisted.web.resource import Resource
from visionUtils import GetPNG, Dist
import pymongo as pm
from utils import GetOrDefault
import simplejson
from bson.objectid import ObjectId
from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor
from twisted.python import log
from caches import Caches, ICache

mf = registry.getComponent(ICache)
if not mf:
    mf = Caches()
    registry.setComponent(ICache, mf)
    
class EntityGet(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
        
    def _delayedRender(self, request):
        # get parmeters from request
        args = request.args
        collName  = GetOrDefault(args, 'entityCollectionName', 'MouthBig')
        query     = GetOrDefault(args, 'sSearch', None, lambda x: eval(x))
        nSkip     = GetOrDefault(args, 'iDisplayStart', 0, lambda x: int(x))
        nLimit    = GetOrDefault(args, 'iDisplayLength', 10, lambda x: int(x))
        sEcho     = GetOrDefault(args, 'sEcho', '1', lambda x:int(x))
        
        conn = pm.Connection("localhost")
        db = conn.DataSet
        coll = db[collName]
        total = coll.count()
        dataCursor = coll.find(query, {"_id":1,"Name":1,"Age":1,"Gender":1,"AvgDistance":1,"MouthFrames.Frame":1}).skip(nSkip).limit(nLimit)
        data = map(lambda x: {"id":str(x["_id"]), "Subject":x["Name"], "Age":x["Age"], "Gender":x["Gender"], "Distance":x["AvgDistance"], "Accuracy":0.0, "#Frames":len(x["MouthFrames"])},
                   dataCursor)

        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours

        simplejson.dump(
        {
            "iTotalRecords" : total,
            "iTotalDisplayRecords" : total,
            "sEcho" : sEcho,
            "aaData" : data
        }, request)
        request.finish()
        
class EntityDetail(Resource):
    def __init__(self, delayTime = 0.1):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
        
    def _delayedRender(self, request):
        return 'entity detail success'

class EntitySaveFrames(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
        
    def _delayedRender(self, request):
        args = request.args
        entityId  = GetOrDefault(args, 'entityId', '')
        collName  = GetOrDefault(args, 'entityCollectionName', 'MouthBig')

        try:
            if entityId in mf.entities:
                log.msg("[ENTITY] Session contains {0}".format(entityId))
                ent = mf.entities[entityId]
                conn = pm.Connection("localhost")
                db = conn.DataSet
                coll = db[collName]
                coll.save(ent)
                log.msg("[ENTITY] Entity saved")
                simplejson.dump(
                {
                    "success" : True,
                }, request)
            else:
                log.err("[ENTITY] {0} not found for save".format(entityId))
                simplejson.dump(
                {
                    "success" : False,
                }, request)
        except:
            log.err("[ENTITY] Saving {0} failed".format(entityId))
            simplejson.dump(
            {
                "success" : False,
            }, request)

        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours
        request.finish()
    
class EntityGetFrames(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
        
    def _delayedRender(self, request):
        args = request.args
        entityId  = GetOrDefault(args, 'entityId', '')
        collName  = GetOrDefault(args, 'entityCollectionName', 'MouthBig')
        query     = GetOrDefault(args, 'sSearch', None, lambda x: eval(x))
        nSkip     = GetOrDefault(args, 'iDisplayStart', 0, lambda x: int(x))
        nLimit    = GetOrDefault(args, 'iDisplayLength', 10, lambda x: int(x))
        sEcho     = GetOrDefault(args, 'sEcho', '1', lambda x:int(x))

        try:
            if entityId in mf.entities:
                log.msg("[ENTITY] Session contains {0}".format(entityId))
                mouthFrames = mf.entities[entityId]["MouthFrames"]
            else:
                log.msg("[ENTITY] Retrieving database {0}".format(entityId))
                if query is None: query = {}
                query["_id"] = ObjectId(entityId)
                conn = pm.Connection("localhost")
                db = conn.DataSet
                coll = db[collName]
                ent = coll.find_one(query)
                mf.entities[entityId] = ent
                mouthFrames = ent["MouthFrames"]
            total = len(mouthFrames)
            url = "http://10.137.168.196:8080/entity.rpy/image"
            data = []
            log.msg("[ENTIYT] entityId = {0}".format(entityId))
            log.msg("[ENTITY] total = {0}".format(total))
            log.msg("[ENTITY] nSkip = {0}".format(nSkip))
            log.msg("[ENTITY] nLmit = {0}".format(nLimit))
            for i in range(nSkip, nSkip + nLimit):
                x = mouthFrames[i]
                log.msg("[ENTITY] i = {0}".format(i))
                data.append({"FrameId"    : i,
                             "FrameNum"   : x["Frame"],
                             "IRMouth"    : "<img class='irimg' src='{0}?frameId={1}&entityId={2}&IRColor={3}'>".format(url, i, entityId, 0),
                             "ColorMouth" : "<img class='colorimg' src='{0}?frameId={1}&entityId={2}&IRColor={3}'>".format(url, i, entityId, 1),
                             "Score":GetOrDefault(x, "Score", 0.0, lambda x: float(x)),
                             "Label":GetOrDefault(x, "Label", 0, lambda x: int(x))})
        except:
            data = []
            total = 0

        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours
        
        simplejson.dump(
        {
            "iTotalRecords" : total,
            "iTotalDisplayRecords" : total,
            "sEcho" : sEcho,
            "aaData" : data
        }, request)
        request.finish()
        
class EntityImage(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
    
    def getClosestFeatureVector(self, y, frame):
        minDist = 1000
        minBox = None
        try:
            for mouthBox in frame["MouthBoxes"]:
                dist = Dist(y, mouthBox["BoxRect"])
                if (dist < minDist):
                    minDist = dist
                    minBox = mouthBox
            return minBox["Features"]
        except:
            return []
        
    def _delayedRender(self, request):
        args = request.args 
        entityId  = GetOrDefault(args, 'entityId', '')
        frameId   = GetOrDefault(args, 'frameId', 0, lambda x: int(x))
        IRorColor = GetOrDefault(args, 'IRColor', 0, lambda x: int(x))
        className = GetOrDefault(args, 'className', 'upperLip')
        image = []
        if entityId in mf.entities:
            mouthFrames = mf.entities[entityId]["MouthFrames"]
            if frameId < len(mouthFrames):
                mouthFrame = mouthFrames[frameId]
                if IRorColor == 1:
                    imageFrame = mouthFrame["ColorImage"]
                else:
                    imageFrame = mouthFrame["IRImage"]
                pixels = imageFrame["pixels"]
                imgtop = imageFrame["top"]
                lMouthy = mouthFrame["FacePoints"]["LeftMouth"][1]
                rMouthy = mouthFrame["FacePoints"]["RightMouth"][1]
                top     = mouthFrame["IRImage"]["top"]
                mMouthy = (lMouthy + rMouthy) / 2.0 - top
                if className in mouthFrame:
                    log.msg("[ENTITY] {0} contains {1}".format(entityId, className))
                target = mMouthy + GetOrDefault(mouthFrame, className, 0, lambda x: int(x))
                log.msg("[ENTITY]Target : {0}".format(target))
                image = GetPNG(pixels, target, self.getClosestFeatureVector(target + imgtop, mouthFrame))
            
        request.setHeader('Content-Type', 'image/png')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours
        
        request.write(image)
        request.finish()

resource = Resource()
resource.putChild("get",       EntityGet())
resource.putChild("detail",    EntityDetail())
resource.putChild("save",      EntitySaveFrames())
resource.putChild("getFrames", EntityGetFrames())
resource.putChild("image",     EntityImage())