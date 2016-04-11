# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
import base
import constants as cons
import crane
from relation import MatchingRelation
from monk.utils.utils import binary2decimal, translate, monitor_accuracy
from monk.math.cmath import sign0
#from itertools import izip
import logging
import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
logger = logging.getLogger("monk.turtle")
metricLog = logging.getLogger("metric")

stopwords_english = set(stopwords.words('english'))
symbols = {'\'', '\"', '[', ']','{','}','(',')','.','$', '#'}

class Turtle(base.MONKObject):
    FPANDAS               = 'pandas'
    FTIGRESS              = 'tigress'
    FMAPPING              = 'mapping'
    FDESCRIPTION          = 'description'
    FPENALTY              = 'pPenalty'
    FEPS                  = 'pEPS'
    FMAXPATHLENGTH        = 'pMaxPathLength'
    FMAXINFERENCESTEPS    = 'pMaxInferenceSteps'
    FPARTIALBARRIER       = 'pPartialBarrier'
    FMERGECLOCK           = 'pMergeClock'
    FTRAINCLOCK           = 'pTrainClock'
    FENTITYCOLLECTIONNAME = 'entityCollectionName'
    FREQUIRES             = 'requires'
    FREQUIRES_UIDS        = 'uids'
    FREQUIRES_TURTLES     = 'turtles'
    FFOLLOWERS            = 'followers'
    FLEADER               = 'leader'
    store = crane.turtleStore
    
    def __default__(self):
        super(Turtle, self).__default__()
        self.pandas = []
        self.tigress = None
        self.mapping = {}
        self.description = cons.DEFAULT_EMPTY
        self.pPenalty = 1.0
        self.pEPS = 1e-6
        self.pMaxPathLength = 1
        self.pMaxInferenceSteps = 1000
        self.entityCollectionName = cons.DEFAULT_EMPTY
        self.requires = dict()
        self.followers = []
        self.leader = None
        self.mergeQueue = set()
        self.pPartialBarrier = 50
        self.pMergeClock = 0
        self.pTrainClock = 0
        
    def __restore__(self):
        super(Turtle, self).__restore__()
        try:
            [panda.setdefault(self.CREATOR, self.creator) for panda in self.pandas]
            [panda.setdefault(self.NAME, self.name) for panda in self.pandas]
            self.tigress.setdefault(self.CREATOR, self.creator)
            self.tigress.setdefault(self.NAME, self.name)
        except:
            pass
        self.pandas = crane.pandaStore.load_or_create_all(self.pandas)
        self.tigress = crane.tigressStore.load_or_create(self.tigress)
        self.pandaUids = set((p.uid for p in self.pandas))
        self.invertedMapping = {tuple(v): k for k, v in self.mapping.iteritems()}
        self.followers = set(self.followers)
        
        if self.FREQUIRES_UIDS in self.requires:
            uids = self.requires[self.FREQUIRES_UIDS]
            if isinstance(uids, basestring):
                uids = eval(uids)
            [panda.add_features(uids) for panda in self.pandas]
        elif self.FREQUIRES_TURTLES in self.requires:
            turtles = self.store.load_or_create_all(
                      [{'name':t, 'creator':self.creator}
                       for t in self.requires[self.FREQUIRES_TURTLES]])
            [panda.add_features(turtle.get_panda_uids()) for turtle in turtles for panda in self.pandas]
        elif self.requires:
            logger.error('dependent features are either in {0} or {1}, but not in {2}'.format(
                         self.FREQUIRES_UIDS,
                         self.FREQUIRES_TURTLES,
                         self.requires))

    def generic(self):
        result = super(Turtle, self).generic()
        if self.tigress:
            result[self.FTIGRESS] = self.tigress.signature()
        result[self.FPANDAS]    = [panda.signature() for panda in self.pandas]
        result[self.FFOLLOWERS] = list(self.followers)
        # invertedMapping is created from mapping
        del result['invertedMapping']
        del result['pandaUids']
        del result['mergeQueue']
        return result
    
    def clone(self, userName):
        obj = super(Turtle, self).clone(userName)
        obj.pandaUids = set(self.pandaUids)
        obj.tigress   = self.tigress.clone(userName)
        obj.pandas    = [p.clone(userName) for p in self.pandas]
        obj.requires  = dict(self.requires)
        return obj
        
    def save(self):
        super(Turtle, self).save()
        if self.tigress:
            self.tigress.save()
        [pa.save() for pa in self.pandas]
        
    def delete(self, deep=False):
        result = super(Turtle, self).delete()
        if self.tigress:
            result = result and self.tigress.delete()
        if deep:
            result = result and [pa.delete() for pa in self.pandas]
        return result
    
    def add_follower(self, follower):
        if follower not in self.followers:
            self.followers.add(follower)
            self.store.push_one_in_fields(self, {'followers':follower})
            [pa.increment() for pa in self.pandas]
            return True
        else:
            logger.info('user {} is already a follower of {}'.format(follower, self.creator))
            return False
            
    def add_leader(self, leader):
        if self.leader != leader:
            self.leader = leader
            self.store.update_one_in_fields(self, {'leader': leader})
            return True
        else:
            logger.info('user {} is already the leader of {}'.format(leader, self.creator))
            return False
            
    def remove_leader(self, leader):
        if self.leader and leader == self.leader:
            self.leader = None
            self.store.update_one_in_fields(self, {'leader':None})
            return True
        else:
            logger.info('user {} is not the leader of {}@{}'.format(leader, self.name, self.creator))
            return False
            
    def remove_follower(self, follower):
        if follower in self.followers:
            self.followers.remove(follower)
            self.store.pull_one_in_fields(self, {'followers':follower})
            [pa.decrease() for pa in self.pandas]
            return True
        else:
            logger.info('user {} is not a follower of {}@{}'.format(follower, self.name, self.crcreator))
            return False
        
    def require_panda(self, panda):
        if self.has_panda(panda):
            logger.error('turtle can not depends on itself {0}'.format(panda._id))
            return
        [pa.add_features(panda.uid) for pa in self.pandas]
        
    def require(self, turtleName):
        if self.name == turtleName:
            logger.error('turle can not depend on itself {0}'.format(turtleName))
            return
        turtle = self.store.load_or_create({'name':turtleName, 'creator':self.creator})
        [panda.add_features(turtle.get_panda_uids()) for panda in self.pandas]
        
    def get_panda_uids(self):
        return [pa.uid for pa in self.pandas]
    
    def has_panda(self, panda):
        return panda.uid in self.pandaUids
        
    def add_panda(self, panda):
        if not self.has_panda(panda):
            self.pandas.append(panda)
            self.pandaUids.add(panda.uid)
            crane.pandaStore.push_one_in_fields(self, {'pandas':panda._id})
            return True
        else:
            logger.info('panda {0} is already in the turtle {1}'.format(panda.name, self.name))
            return False
    
    def delete_panda(self, panda):
        if self.has_panda(panda):
            self.pandas.remove(panda)
            self.pandaUids.remove(panda.uid)
            crane.pandaStore.pull_one_in_fields(self, {'pandas':panda._id})
            return True
        else:
            logger.info('panda {0} is not in the turtle {1}'.format(panda.name, self.name))
            return False

    def predict(self, entity, fields=None):
        scores = [panda.predict(entity) for panda in self.pandas]
        predicted = self.invertedMapping[tuple(map(sign0, scores))]
        self.tigress.measure(entity, predicted)
        return predicted
        
    def test_data(self, entity):
        test = [panda.predict(entity) for panda in self.pandas]
        logger.info('turtle {0} value is {1}'.format(self.creator, test[0]))
        return test    

    def add_data(self, entity):
        return self.tigress.supervise(self, entity)
    
    def active_train(self):
        try:
            self.tigress.supervise(self)
        except Exception as e:
            logger.info(e.message)
            logger.info("turtle {0} does not have active superviser".format(self.name))
    
    def train(self):
        [panda.train(self.leader) for panda in self.pandas]
        self.pTrainClock += 1
        self.update_fields({self.FTRAINCLOCK:self.pTrainClock})
        logger.debug('training clock {0}'.format(self.pTrainClock))
    
    def checkout(self):
        [panda.checkout(self.leader) for panda in self.pandas]

    def commit(self):
        [panda.commit() for panda in self.pandas]
        
    def merge(self, follower):
        if follower not in self.followers and follower != self.creator:
            logger.error('user {0} is not a follower of {1}@{2}'.format(follower, self.creator, self.name))
            return False
        self.mergeQueue.add(follower)
        if len(self.mergeQueue) >= min(len(self.followers), self.pPartialBarrier):
            for follower in self.mergeQueue:
                [panda.merge(follower) for panda in self.pandas]               
            self.mergeQueue.clear()
            [panda.update_fields({panda.FCONSENSUS:panda.z.generic()}) for panda in self.pandas]
            self.pMergeClock += 1
            self.update_fields({self.FMERGECLOCK:self.pMergeClock})
            logger.debug('merge clock {0}'.format(self.pMergeClock))
            return True
        return False
    
    def reset(self):
        [panda.reset() for panda in self.pandas]
        self.pTrainClock = 0
        self.pMergeClock = 0
        self.update_fields({self.FTRAINCLOCK:self.pTrainClock, self.FMERGECLOCK:self.pMergeClock})
        
    def reset_data(self):
        [panda.reset_data() for panda in self.pandas] 

    def set_mantis_parameter(self, para, value):
        [panda.set_mantis_parameter(para, value) for panda in self.pandas]                   
        
class SingleTurtle(Turtle):
    
    def predict(self, entity, fields=None):
        panda = self.pandas[0]
        score = panda.predict(entity)
        if sign0(score) > 0:
            self.tigress.measure(entity, panda.name)
            monitor_accuracy(panda.name, self.creator, score, 'True')
            return panda.name
        else:
            self.tigress.measure(entity, cons.DEFAULT_NONE)
            monitor_accuracy(panda.name, self.creator, score, 'False')
            return cons.DEFAULT_NONE
        
class MultiLabelTurtle(Turtle):

    def predict(self, entity, fields=None):
        predicted = [panda.name for panda in self.pandas if panda.predict(entity) > 0]
        self.tigress.measure(entity, predicted)
        return predicted
        
class RankingTurtle(Turtle):
    FTARGET_CONNECTION_STRING = 'targetConnectionString'
    FTARGET_DATABASE_NAME     = 'targetDatabaseName'
    FTARGET_COLLECTION_NAME   = 'targetCollectionName'
    FTARGET_NUM_LEVELS        = 'numLevels'
    FBEAM_SIZE                = 'beamSize'
    FWINDOW_SIZE              = 'windowSize'
    FQUERY                    = 'queryFunc'
    FTARGET_STORE             = 'targetStore'
    RAW_TARGETID              = '_targetId'
    RAW_RELEVANCE             = '_relevance'
    
    def __default__(self):
        super(RankingTurtle, self).__default__()
        self.targetConnectionString = cons.DEFAULT_EMPTY
        self.targetDatabaseName     = cons.DEFAULT_EMPTY
        self.targetCollectionName   = cons.DEFAULT_EMPTY
        self.targetStore = crane.Crane()
        self.numLevels   = 1
        self.beamSize    = 10
        self.windowSize  = 2 * self.beamSize
        self.queryFunc   = cons.DEFAULT_FUNC
    
    def __restore__(self):
        super(RankingTurtle, self).__restore__()
        self.targetStore = crane.Crane(self.targetConnectionString,
                                       self.targetDatabaseName,
                                       self.targetCollectionName)
        
    def generic(self):
        result = super(RankingTurtle, self).generic()
        del result[self.FTARGET_STORE]
        return result
    
    def clone(self, userName):
        obj = super(RankingTurtle, self).clone(userName) 
        return obj
        
    def predict(self, entity, fields=None):
        query = eval(self.queryFunc)(entity)
        targetIds = self.targetStore.load_all_in_ids(query, 0, self.windowSize)
        targets = self.targetStore.load_all_by_ids(targetIds)
        relation = MatchingRelation()
        relation.set_argument(0, entity)
        results = []
        for target in targets:
            relation.set_argument(1, target)
            relation.compute()
            rank = self.invertedMapping[[sign0(panda.predict(relation)) for panda in self.pandas]]
            results.append((rank, target))
        results.sort(reverse=True)
        return results[:self.beamSize]
    
    def add_data(self, entity):
        targetId = entity.get_raw(self.RAW_TARGETID, None)
        relevance = entity.get_raw(self.RAW_RELEVANCE, 0)
        if targetId:
            target = self.targetStore.load_one_by_id(targetId)
            relation = MatchingRelation()
            relation.set_argument(0, entity)
            relation.set_argument(1, target)
            relation.compute()
            relation.set_raw(self.RAW_RELEVANCE, relevance)
            self.tigress.supervise(self, relation)
        
class SPNTurtle(Turtle):
    pass

class DictionaryTurtle(Turtle):

    def __default__(self):
        super(DictionaryTurtle, self).__default__()
        self.dictionary = dict()
        
    def __restore__(self):
        super(DictionaryTurtle, self).__restore__()
        self.dictionary = {p.name:p.uid for p in self.pandas}
        
    def generic(self):
        result = super(DictionaryTurtle, self).generic()
        try:
            del result['tigress']
            del result['dictionary']
        except:
            pass
        return result
    
    def clone(self, userName):
        obj = super(DictionaryTurtle, self).clone(userName)
        obj.dictionary = dict(self.dictionary)
        return obj
        
    def _process(self, field):
        return {}
    
    def _get_or_new_panda(self, name):
        if name not in self.dictionary:
            panda = {self.MONK_TYPE: 'ExistPanda',
                     self.NAME: name,
                     self.CREATOR: self.creator}
            panda = crane.pandaStore.load_or_create(panda, tosave=True)
            self.add_panda(panda)
            self.dictionary[name] = panda.uid
            uid = panda.uid
        else:
            uid = self.dictionary[name]
        return (uid, 1.0)
    
    def is_stop(self, w):
        if w in stopwords_english:
            return True
        else:
            return False
            
    def is_symbol(self, w):
        if w in symbols:
            return True
        elif w.find('.') >= 0:
            return True
        else:
            return False
    
    def is_single(self, w):
        if len(w) <= 1:
            return True
        else:
            return False
            
    def predict(self, entity, fields):
        total = 0
        for field in fields:
            value = translate(getattr(entity, field, ''))
            if not value:
                continue
            
            allTokens = self._process(value)
            entity._raws.update(allTokens)
            entity._features.update([self._get_or_new_panda(t) for t in allTokens])
            total += len(allTokens)

        return total
    
    def merge(self):
        # TODO should be taking care of dedups in models and data
        pass
    
class UniGramTurtle(DictionaryTurtle):

    def _process(self, field):
        allTokens = {}
        sents = nltk.tokenize.sent_tokenize(field)
        for sent in sents:
            tokens = nltk.tokenize.word_tokenize(sent.lower())
            allTokens.update(((t,1) for t in tokens if not self.is_stop(t) and
                                                       not self.is_symbol(t) and
                                                       not self.is_single(t)))
        return allTokens
    
class POSTurtle(DictionaryTurtle):
    
    def _process(self, field):
        allTokens = {}
        sents = nltk.tokenize.sent_tokenize(field)
        for sent in sents:
            tokens = nltk.tokenize.word_tokenize(sent.lower())
            tagged = nltk.pos_tag([t for t in tokens if not self.is_stop(t) and
                                                        not self.is_symbol(t) and
                                                        not self.is_single(t)])
            allTokens.update((('_'.join(t),1) for t in tagged))
        return allTokens

class StemTurtle(DictionaryTurtle):

    def _process(self, field):
        allTokens = {}
        sents = nltk.tokenize.sent_tokenize(field)
        logger.debug(sents)
        port = PorterStemmer()
        for sent in sents:
            tokens = nltk.tokenize.word_tokenize(sent.lower())
            stems = [port.stem(t) for t in tokens if not self.is_stop(t) and not self.is_symbol(t)]
            allTokens.update(((t,1) for t in stems))
        logger.debug(' '.join(allTokens))
        return allTokens
        
base.register(Turtle)
base.register(SingleTurtle)
base.register(MultiLabelTurtle)
base.register(RankingTurtle)
base.register(DictionaryTurtle)
base.register(SPNTurtle)
base.register(UniGramTurtle)
base.register(POSTurtle)
base.register(StemTurtle)
