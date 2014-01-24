# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 15:36:19 2013

@author: xumiao
"""
from twisted.web.resource import Resource
import simplejson
from utils import GetOrDefault,Serialize,Deserialize
from twisted.web.server import NOT_DONE_YET
from bson.objectid import ObjectId
from twisted.internet import reactor
from twisted.python import log
import pymongo as pm
import numpy as np
import sklearn.ensemble as ens
import sklearn.svm as svm
from caches import Caches, ICache

mf = registry.getComponent(ICache)
if not mf:
    mf = Caches()
    registry.setComponent(ICache, mf)

class PandaAdd(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET

    def insertPanda(self, args):
        conn = pm.Connection("localhost")
        db = conn.DataSet
        coll = db.Models
        Name           = GetOrDefault(args, "pandaName", None)
        ClassifierType = GetOrDefault(args, "pandaType", None)
        ClassName      = GetOrDefault(args, "className", None)
        Slicing        = GetOrDefault(args, "slicing", "{}")
        Parameters     = GetOrDefault(args, "parameters", "{}")
        if Name is None or ClassName is None:
            return None
            
        idstr = str(coll.insert({"Name": Name,\
                                 "ClassifierType": ClassifierType,\
                                 "ClassName": ClassName,\
                                 "Slicing": Slicing,\
                                 "Parameters": Parameters,\
                                 "Accuracy": 0.0,\
                                 "Experience": 0}))
        log.msg("[PANDA] classifier created")
        return {
          "id"        : idstr,\
          "name"      : Name,\
          "type"      : ClassifierType,\
          "className" : ClassName,\
          "slicing"   : Slicing,\
          "parameters": Parameters,\
          "accuracy"  : 0.0,\
          "experience": 0,\
          "status"    : "idle"}
        
    def _delayedRender(self, request):
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours        
        args = request.args
        try:
            panda = self.insertPanda(args)
            mf.pandas[panda["id"]] = panda
            simplejson.dump(
            {
                "success" : True
            }, request)
        except Exception as e:
            simplejson.dump(
            {
                "success" : False,
                "message" : repr(e)
            }, request)
        request.finish()
        
class PandaSave(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
    
    def updatePanda(self, panda):
        conn = pm.Connection("localhost")
        db = conn.DataSet
        coll = db.Models
        coll.update({"_id":ObjectId(panda["id"])},\
                    {"_id":ObjectId(panda["id"]),\
                     "Name"           :panda["name"],\
                     "ClassifierType" :panda["type"],\
                     "ClassName"      :panda["className"],\
                     "Slicing"        :panda["slicing"],\
                     "Parameters"     :panda["parameters"],\
                     "Classifier"     :Serialize(panda["classifier"]),\
                     "Accuracy"       :panda["accuracy"],\
                     "Experience"     :panda["experience"]})
                     
        log.msg("[PANDA] panda updated")
        
    def _delayedRender(self, request):
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours        
        # get parmeters from request
        args = request.args
        idstr = GetOrDefault(args, 'pandaId', '')
        
        try:
            panda = mf.pandas[idstr]
            log.msg("[PANDA] found {0}".format(idstr))
            self.updatePanda(panda)
            simplejson.dump(
            {
                "success" : True
            }, request)
        except Exception as e:
            simplejson.dump(
            {
                "success" : False,
                "message" : repr(e)
            }, request)

        request.finish()
        
class PandaDel(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
        
    def _delayedRender(self, request):
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours
        
        simplejson.dump(
        {
            "success" : "done"
        }, request)
        request.finish()
    
class PandaGet(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
    
    def _getPanda(self, x, pandas):
        idstr = GetOrDefault(x, "_id", "", str)
        log.msg("[PANDA] get id {0}".format(idstr))
        if idstr in pandas:
            return pandas[idstr]
        else:
            panda = {
              "id"        : idstr,\
              "name"      : GetOrDefault(x, "Name", "", str),\
              "type"      : GetOrDefault(x, "ClassifierType", "RandomForest", str),\
              "className" : GetOrDefault(x, "ClassName", "", str),\
              "slicing"   : GetOrDefault(x, "Slicing", "{}", str),\
              "parameters": GetOrDefault(x, "Parameters", "{}", str),\
              "accuracy"  : GetOrDefault(x, "Accuracy", 0.0, lambda x:float(x)),\
              "experience": GetOrDefault(x, "Experience", 0, lambda x:int(x)),\
              "classifier": GetOrDefault(x, "Classifier", None, Deserialize),\
              "status"    : "idle"
            }
            log.msg("[PANDA] get {0}".format(panda))
            pandas[idstr] = panda
            log.msg("[PANDA] {0} added to session".format(idstr))
            return panda
        
    def _delayedRender(self, request):
        # get parmeters from request
        args = request.args
        query     = GetOrDefault(args, 'sSearch', None, lambda x: eval(x))
        nSkip     = GetOrDefault(args, 'iDisplayStart', 0, lambda x: int(x))
        nLimit    = GetOrDefault(args, 'iDisplayLength', 10, lambda x: int(x))
        sEcho     = GetOrDefault(args, 'sEcho', '1', lambda x:int(x))
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours
        
        try:
            conn = pm.Connection("localhost")
            db = conn.DataSet
            coll = db.Models
            total = coll.count()
            dataCursor = coll.find(query, {"_id":1,\
                                           "Name":1,\
                                           "ClassifierType":1,\
                                           "Slicing":1,\
                                           "Parameters":1,\
                                           "Accuracy":1,\
                                           "Experience":1,\
                                           "ClassName":1,\
                                           "Classifier":1})\
                            .skip(nSkip).limit(nLimit)
            log.msg("[PANDA] panda found")
            pandas = map(lambda x: self._getPanda(x, mf.pandas), dataCursor)
            log.msg("[PANDA] get pandas")
            simplejson.dump(
            {
                "iTotalRecords" : total,
                "iTotalDisplayRecords" : total,
                "sEcho" : sEcho,
                "aaData" : map(lambda x: {"id"        : x["id"],\
                                          "name"      : x["name"],\
                                          "type"      : x["type"],\
                                          "className" : x["className"],\
                                          "slicing"   : x["slicing"],\
                                          "parameters": x["parameters"],\
                                          "accuracy"  : x["accuracy"],\
                                          "experience": x["experience"],\
                                          "status"    : x["status"]}, pandas)
            }, request)
        except:
            simplejson.dump(
            {
                "iTotalRecords" : 0,
                "iTotalDisplayRecords" : 0,
                "sEcho" : sEcho,
                "aaData" : []
            }, request)
            

        request.finish()
        
class PandaLoad(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
    
    def loadClassifier(self, panda):
        typeName = GetOrDefault(panda, "type", "")
        params   = GetOrDefault(panda , "parameters", "{}", eval)
        
        log.msg("[PANDA] before creating classifier, {0}".format(typeName))
        log.msg("[PANDA] params, {0}".format(params))
        
        if typeName == "RandomForest":
            n_estimators      = GetOrDefault(params, "n_estimators", 100, lambda x: int(x))
            criterion         = GetOrDefault(params, "criterion", "gini")
            max_depth         = GetOrDefault(params, "max_depth", 10, lambda x: int(x))
            min_samples_split = GetOrDefault(params, "min_samples_split", 10, lambda x: int(x))
            min_samples_leaf  = GetOrDefault(params, "min_samples_leaf", 5, lambda x: int(x))
            bootstrap         = GetOrDefault(params, "bootstrap", True, lambda x: bool(x))
            n_jobs            = GetOrDefault(params, "n_jobs", -1, lambda x: int(x))
            oob_score         = GetOrDefault(params, "oob_score", False, lambda x: bool(x))
            max_features      = GetOrDefault(params, "max_features", "auto")
            classifier = ens.RandomForestClassifier(n_estimators = n_estimators,\
                                                     criterion = criterion,\
                                                     max_depth = max_depth,\
                                                     min_samples_split = min_samples_split,\
                                                     min_samples_leaf = min_samples_leaf,\
                                                     bootstrap = bootstrap,\
                                                     oob_score = oob_score,\
                                                     n_jobs = n_jobs,\
                                                     max_features = max_features)
        elif typeName == "LinearSVM":
            C       = GetOrDefault(params, "C", 1.0, lambda x: float(x))
            loss    = GetOrDefault(params, "loss", "l2")
            penalty = GetOrDefault(params, "penalty", "l2")
            dual    = GetOrDefault(params, "dual", True, lambda x: bool(x))
            tol     = GetOrDefault(params, "tol", 0.001, lambda x: float(x))
            classifier = svm.LinearSVC(penalty = penalty,\
                                        loss = loss,\
                                        dual = dual,\
                                        tol = tol,\
                                        C = C,\
                                        fit_intercept=True,\
                                        intercept_scaling = 1,\
                                        class_weight = "auto")
        elif typeName == "KernelSVM":
            C          = GetOrDefault(params, "C", 1.0, lambda x: float(x))
            kernel     = GetOrDefault(params, "kernel", "rbf")
            degree     = GetOrDefault(params, "degree", 3, lambda x: int(x))
            gamma      = GetOrDefault(params, "gamma", 0.0, lambda x: float(x))
            coef0      = GetOrDefault(params, "coef0", 0.0, lambda x: float(x))
            shrinking  = GetOrDefault(params, "shrinking", True, lambda x: bool(x))
            tol        = GetOrDefault(params, "tol", 0.001, lambda x: float(x))
            cache_size = GetOrDefault(params, "cache_size", None, lambda x: float(x))
            max_iter   = GetOrDefault(params, "max_iter", -1, lambda x: int(x))
            classifier = svm.SVC(C = C,\
                                  kernel = kernel,\
                                  degree = degree,\
                                  gamma = gamma,\
                                  coef0 = coef0,\
                                  shrinking = shrinking,\
                                  probability = False,\
                                  tol = tol,\
                                  cache_size = cache_size,\
                                  class_weight = "auto",\
                                  max_iter = max_iter)        
        panda["classifier"] = classifier
        
    def loadData(self, panda, mf):
        pass
    
    def _delayedRender(self, request):
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours
        # get parmeters from request
        args = request.args
        pandaId = GetOrDefault(args, 'pandaId', '')
        try:
            panda = mf.pandas[pandaId]
            log.msg("[PANDA] load panda {0}".format(pandaId))
            classifier = GetOrDefault(panda, "classifier", None)
            if classifier is None:
                self.loadClassifier(panda)
                log.msg("[PANDA] classifier ready")
                panda["status"] = "ready"
                message = "ready"
            else:
                log.msg("[PANDA] already ready")
                message = "stay the same"
            simplejson.dump(
            {
                "success" : True,
                "message" : message
            }, request)
        except Exception as e:
            simplejson.dump(
            {
                "success" : False,
                "message" : repr(e)
            }, request)
            
        request.finish()


class PandaTag(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
        
    def _delayedRender(self, request):
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours
        args = request.args
        entityId  = GetOrDefault(args, 'entityId', '')
        frameId   = GetOrDefault(args, 'frameId', 0, lambda x: int(x))
        tagAction = GetOrDefault(args, 'tagAction', -1, lambda x: int(x))
        className = GetOrDefault(args, 'className', 'upperLip')

        if entityId in mf.entities:
            log.msg("[PANDA] Session has entity {0}".format(entityId))
            ent = mf.entities[entityId]
            frame = ent["MouthFrames"][frameId]
            if className in frame:
                log.msg("[PANDA]Target value before = {0}".format(frame[className]))
                frame[className] += tagAction
                log.msg("[PANDA]Target value after  = {0}".format(frame[className]))
            else:
                log.msg("[PANDA]Target value before = 0 (default)")
                frame[className] = tagAction
                log.msg("[PANDA]Target value after  = {0}".format(frame[className]))
            simplejson.dump(
            {
                "success" : True,
                "className" : className,
                "target" : frame[className]
            }, request)
        else:
            simplejson.dump(
            {
                "success" : False,
                "message" : "{0} not found ".format(entityId)
            }, request)
            
        request.finish()

class PandaStatus(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
        
    def _delayedRender(self, request):
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours        
        args = request.args
        pandaId  = GetOrDefault(args, 'pandaId', '')

        if pandaId in mf.pandas:
            log.msg("[PANDA] Panda {0} found".format(pandaId))
            panda = mf.pandas[pandaId]
            simplejson.dump(
            {
                "status" : panda["status"]
            }, request)
        else:
            simplejson.dump(
            {
                "status" : "unknown"
            }, request)
            
        request.finish()
        
class PandaTrain(Resource):
    def __init__(self, delayTime = 0.0):
        self.delayTime = delayTime
 
    def render_GET(self, request):
        reactor.callLater(self.delayTime, self._delayedRender, request)
        return NOT_DONE_YET
    
    def _train(self, panda, x, y):
        classifier = panda["classifier"]
        classifier.fit(x,y)
        panda["status"] = "ready"
        
    def _delayedRender(self, request):
        request.setHeader('Content-Type', 'json')
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        request.setHeader('Access-Control-Max-Age', "2520") # 42 hours        
        args = request.args
        pandaId  = GetOrDefault(args, 'pandaId', '')

        if pandaId in mf.pandas and pandaId not in mf.queue:
            log.msg("[PANDA] Panda {0} found".format(pandaId))
            panda = mf.pandas[pandaId]
            panda["status"] = "training..."
            #load data
            #schedule a training call
            callid = reactor.callLater(0.1, self.train, panda, x, y)
            mf.queue[pandaId] = callid
#            frame = ent["MouthFrames"][frameId]
#            if className in frame:
#                log.msg("[PANDA]Target value before = {0}".format(frame[className]))
#                frame[className] += tagAction
#                log.msg("[PANDA]Target value after  = {0}".format(frame[className]))
#            else:
#                log.msg("[PANDA]Target value before = 0 (default)")
#                frame[className] = tagAction
#                log.msg("[PANDA]Target value after  = {0}".format(frame[className]))
            simplejson.dump(
            {
                "success" : True,
            }, request)
        else:
            simplejson.dump(
            {
                "success" : False,
            }, request)
            
        request.finish()
        
resource = Resource()
resource.putChild("get",   PandaGet())
resource.putChild("save",  PandaSave())
resource.putChild("load",  PandaLoad())
resource.putChild("train", PandaTrain())
resource.putChild("add",   PandaAdd())
resource.putChild("del",   PandaDel())
resource.putChild("tag",   PandaTag())
resource.putChild("status", PandaStatus())
