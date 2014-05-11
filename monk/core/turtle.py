# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
import base
import constants as cons
import crane
from ..math.cmath import sign0
#from itertools import izip
import logging
import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from monk.utils.utils import translate

logger = logging.getLogger("monk.turtle")

stopwords_english = set(stopwords.words('english'))
symbols = {'\'', '\"', '[', ']','{','}','(',')','.','$', '#'}

class Turtle(base.MONKObject):
    FPANDAS               = 'pandas'
    FTIGRESS              = 'tigress'
    FMAPPING              = 'mapping'
    FNAME                 = 'name'
    FDESCRIPTION          = 'description'
    FPENALTY              = 'pPenalty'
    FEPS                  = 'pEPS'
    FMAXPATHLENGTH        = 'pMaxPathLength'
    FMAXINFERENCESTEPS    = 'pMaxInferenceSteps'
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
        self.name = cons.DEFAULT_EMPTY
        self.description = cons.DEFAULT_EMPTY
        self.pPenalty = 1.0
        self.pEPS = 1e-6
        self.pMaxPathLength = 1
        self.pMaxInferenceSteps = 1000
        self.entityCollectionName = cons.DEFAULT_EMPTY
        self.requires = dict()
        self.followers = set()
        self.leader = None
        
    def __restore__(self):
        super(Turtle, self).__restore__()
        self.pandas = crane.pandaStore.load_or_create_all(self.pandas)
        self.tigress = crane.tigressStore.load_or_create(self.tigress)
        self.pandaUids = set((p.uid for p in self.pandas))
        self.invertedMapping = {v: k for k, v in self.mapping.iteritems()}
        
        if self.FREQUIRES_UIDS in self.requires:
            uids = self.requires[self.FREQUIRES_UIDS]
            if isinstance(uids, basestring):
                uids = eval(uids)
            [panda.add_features(uids) for panda in self.pandas]
        elif self.FREQUIRES_TURTLEIDS in self.requires:
            turtles = self.store.load_all_by_name_user(
                      [(t, self.creator) for t in self.requires[self.FREQUIRES_TURTLES]])
            [panda.add_features(turtle.get_panda_uids()) for turtle in turtles for panda in self.pandas]
        else:
            logger.error('dependent features are either in {0} or {1}, but not in {2}'.format(
                         self.FREQUIRES_UIDS,
                         self.FREQUIRES_TURTLES,
                         self.requires))

    def generic(self):
        result = super(Turtle, self).generic()
        result[self.FTIGRESS] = {'name':self.tigress.name, 'creator':self.tigress.creator}
        result[self.FPANDAS] = [{'name':panda.name, 'creator':panda.creator} for panda in self.pandas]
        # invertedMapping is created from mapping
        del result['invertedMapping']
        del result['pandaUids']
        return result
    
    def clone(self, user):
        obj = super(Turtle, self).clone(user)
        obj.pandaUids = set(self.pandaUids)
        obj.tigress = self.tigress.clone(user)
        obj.pandas = [p.clone(user) for p in self.pandas]
        return obj
        
    def save(self, **kwargs):
        super(Turtle, self).save(kwargs)
        if self.tigress:
            self.tigress.save(kwargs)
        [pa.save(kwargs) for pa in self.pandas]
        
    def delete(self):
        result = super(Turtle, self).delete()
        if self.tigress:
            result = result and self.tigress.delete()
        if self.pandas:
            result = result and [pa.delete() for pa in self.pandas].all()
        return result
    
    def require_panda(self, panda):
        if self.has_panda(panda):
            logger.error('turtle can not depends on itself {0}'.format(panda._id))
            return
        [pa.add_features(panda.uid) for pa in self.pandas]
        
    def require(self, turtleName):
        if self.name == turtleName:
            logger.error('turle can not depend on itself {0}'.format(turtleName))
            return
        turtle = self.store.load_all_by_name_user(turtleName, self.creator)
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
        predicted = self.invertedMapping[tuple([sign0(panda.predict(entity)) for panda in self.pandas])]
        self.tigress.measure(entity, predicted)
        return predicted

    def add_data(self, entity):
        return self.tigress.supervise(self, entity)
    
    def active_train(self):
        try:
            self.tigress.supervise(self)
        except Exception as e:
            logger.info(e.message)
            logger.info("turtle {0} does not have active superviser".format(self.name))
    
    def train(self):
        [panda.mantis.train(self.leader) for panda in self.pandas if panda.has_mantis()]
        [panda.save() for panda in self.pandas]
    
    def merge(self, user):
        if user not in self.followers:
            logger.error('user {0} is not a follower of {1}@{2}'.format(user, self.creator, self.name))
            return False  
        return [panda.mantis.merge(user) for panda in self.pandas if panda.has_mantis()].all()

    def has_user(self, user):
        return self.store.has_user(self.name, user)
    
    def has_user_in_store(self, user):
        return self.store.has_user_in_store(self.name, user)
        
    def add_user(self, user):
        if not self.has_user_in_store(user):
            newTurtle = self.clone(user)
            self.followers.add(user)
            newTurtle.leader = self.creator
            newTurtle.save()
            return newTurtle
        else:
            logger.error('user {0} already has cloned this turtle'.format(user))
            return None
        
    def remove_user(self, user):
        if user is self.creator or user in self.followers:
            return self.delete()
        else:
            # only self or one of the followers can be removed
            logger.error('you {0} dont have the permission to delete user {1} for turtle {2}'.format(
                         self.user, user, self.name))
            return False
    
    def transfer_user(self, user, leader):
        if user not in self.followers:
            logger.error('user {0} is not a follower of {1}@{2}'.format(user, self.creator, self.name))
            return False
        
        leaderTurtle = self.store.load_one_by_name_user(self.name, leader)
        if not leaderTurtle:
            logger.error('leader {0} does not has turtle {1}'.format(leader, self.name))
            return False

        leaderTurtle.followers.add(user)
        user.leader = leader
        self.followers.remove(user)
        return True
            
class SingleTurtle(Turtle):
    
    def predict(self, entity, fields=None):
        panda = self.pandas[0]
        if sign0(panda.predict(entity)) > 0:
            self.tigress.measure(entity, panda.name)
            return panda.name
        else:
            self.tigress.measure(entity, cons.DEFAULT_NONE)
            return cons.DEFAULT_NONE
        
class MultiLabelTurtle(Turtle):

    def predict(self, entity, fields=None):
        predicted = [panda.name for panda in self.pandas if panda.predict(entity) > 0]
        self.tigress.measure(entity, predicted)
        return predicted
        
class RankingTurtle(Turtle):
        
    def predict(self, entity, fields=None):
        pass
    
    def add_data(self, entity):
        pass
    
    def train(self):
        pass
    
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
        del result['tigress']
        del result['dictionary']
        return result
    
    def clone(self, user):
        obj = super(DictionaryTurtle, self).clone(user)
        obj.dictionary = dict(self.dictionary)
        return obj
        
    def _process(self, field):
        return {}
    
    def _get_or_new_panda(self, name):
        if name not in self.dictionary:
            panda = {self.MONK_TYPE: 'ExistPanda',
                     self.FNAME: name,
                     self.CREATOR: self.creator}
            panda = crane.pandaStore.load_create_by_name_user(panda, True)
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
