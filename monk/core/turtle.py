# -*- coding: utf-8 -*-
"""
Created on Fri Nov 08 19:52:01 2013
The complex problem solver that manage a team of pandas. 
@author: xm
"""
import base
import constants
import crane
from bson.objectid import ObjectId
from ..math.cmath import sigmoid, sign0
import tigress as ti
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

    def __restore__(self):
        super(Turtle, self).__restore__()
        if 'pandas' in self.__dict__:
            self.pandas = crane.pandaStore.load_or_create_all(self.pandas)
        else:
            self.pandas = []
        self.pandaUids = set((p.uid for p in self.pandas))
        if 'tigress' in self.__dict__:
            self.tigress = crane.tigressStore.load_or_create(self.tigress)
        else:
            self.tigress = ti.Tigress()
        if "mapping" not in self.__dict__:
            self.mapping = {}
        self.invertedMapping = {v: k for k, v in self.mapping.iteritems()}
        if 'name' not in self.__dict__:
            self.name = constants.DEFAULT_NONE
        if 'description' not in self.__dict__:
            self.description = constants.DEFAULT_NONE
        if 'pPenalty' not in self.__dict__:
            self.pPenalty = 1.0
        if 'pEPS' not in self.__dict__:
            self.pEPS = 1e-8
        if 'pMaxPathLength' not in self.__dict__:
            self.pMaxPathLength = 1
        if 'pMaxInferenceSteps' not in self.__dict__:
            self.pMaxInferenceSteps = 1
        if "entityCollectionName" not in self.__dict__:
            self.entityCollectionName = constants.DEFAULT_EMPTY
        if "requires" not in self.__dict__:
            logger.info('turtle {0} will use all features seen'.format(self.name))
        elif 'uids' in self.requires:
            uids = self.requires['uids']
            if isinstance(uids, basestring):
                uids = eval(uids)
            [panda.add_features(uids) for panda in self.pandas]
        elif 'turtleIds' in self.requires:
            turtles = crane.turtleStore.load_all_by_ids([ObjectId(tid) for tid in self.requires['turtleIds']])
            [panda.add_features(turtle.get_panda_uids()) for turtle in turtles for panda in self.pandas]
        else:
            logger.error('dependent features are either in uids or turtle_ids, but not in {0}'.format(self.requires))

    def generic(self):
        result = super(Turtle, self).generic()
        result['tigress'] = self.tigress._id
        result['pandas'] = [panda._id for panda in self.pandas]
        # invertedMapping is created from mapping
        del result['invertedMapping']
        del result['pandaUids']
        return result
    
    def save(self, **kwargs):
        crane.turtleStore.update_one_in_fields(self, self.generic())
        self.tigress.save()
        [pa.save() for pa in self.pandas]

    def delete(self, deep=False):
        result = crane.turtleStore.delete_by_id(self._id)
        result = result and self.tigress.delete()
        if deep:
            result = result and [pa.delete() for pa in self.pandas].all()
        return result
    
    def require(self, turtleId):
        if self._id is turtleId:
            logger.error('turle can not depend on itself {0}'.format(turtleId))
            return
        turtle = crane.turtleStore.load_all_by_id(turtleId)
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

    def _predict(self, userId, panda, entity):
        entity[panda.uid] = sigmoid(panda.predict(userId, entity))
        return sign0(entity[panda.uid])
        
    def predict(self, userId, entity, fields=None):
        predicted = self.invertedMapping[tuple([self._predict(userId, panda, entity) for panda in self.pandas])]
        self.tigress.measure(userId, entity, predicted)
        return predicted

    def add_data(self, userId, entity):
        return self.tigress.supervise(self, userId, entity)
    
    def active_train_one(self, userId):
        try:
            self.tigress.supervise(self, userId)
        except Exception as e:
            logger.info(e.message)
            logger.info("turtle {0} does not have active superviser".format(self.name))
    
    def train_one(self, userId):
        [panda.mantis.train_one(userId) for panda in self.pandas if panda.has_mantis()]
        [panda.save_one(userId) for panda in self.pandas]
    
    def aggregate(self, userId):
        [panda.mantis.aggregate(userId) for panda in self.pandas if panda.has_mantis()]
    
    def has_user(self, userId):
        if not self.tigress.has_user(userId) or \
            [False for panda in self.pandas if not panda.has_user(userId)]:
            return False
        return True
    
    def has_user_in_store(self, userId):
        if not self.tigress.has_user_in_store(userId) or \
            [False for panda in self.pandas if not panda.has_user_in_store(userId)]:
            return False
        return True

    def not_has_user(self, userId):
        if self.tigress.has_user(userId) or \
            [True for panda in self.pandas if panda.has_user(userId)]:
            return False
        return True
    
    def not_has_user_in_store(self, userId):
        if self.tigress.has_user_in_store(userId) or \
            [True for panda in self.pandas if panda.has_user_in_store(userId)]:
            return False
        return True
        
    def add_one(self, userId):
        if not self.tigress.add_one(userId):
            return False
        
        if [False for panda in self.pandas if not panda.add_one(userId)]:
            return False
            
        return True
    
    def remove_one(self, userId):
        self.tigress.remove_one(userId)
            
        [False for panda in self.pandas if not panda.remove_one(userId)]
            
        return True
        
    def load_one(self, userId):
        if not self.tigress.load_one(userId):
            return False
            
        if [False for panda in self.pandas if not panda.load_one(userId)]:
            return False
            
        return True
    
    def unload_one(self, userId):
        if not self.tigress.unload_one(userId):
            return False
        
        if [False for panda in self.pandas if not panda.unload_one(userId)]:
            return False
        
        return True
        
    def save_one(self, userId):
        if not self.tigress.save_one(userId):
            return False
            
        if [False for panda in self.pandas if not panda.save_one(userId)]:
            return False
        
        return True
    
class SingleTurtle(Turtle):
    
    def predict(self, userId, entity, fields=None):
        panda = self.pandas[0]
        entity[panda.uid] = sigmoid(panda.predict(userId, entity))
        if sign0(entity[panda.uid]) > 0:
            self.tigress.measure(userId, entity, panda.name)
            return panda.name
        else:
            self.tigress.measure(userId, entity, constants.DEFAULT_NONE)
            return constants.DEFAULT_NONE
        
    def train_one(self, userId):
        panda = self.pandas[0]
        if panda.has_mantis():
            panda.mantis.train_one(userId)

class MultiLabelTurtle(Turtle):

    def predict(self, userId, entity, fields=None):
        predicted = [panda.name for panda in self.pandas if self._predict(userId, panda, entity) > 0]
        self.tigress.measure(userId, entity, predicted)
        return predicted
        
class RankingTurtle(Turtle):
        
    def predict(self, userId, entity):
        pass
    
    def add_data(self, userId, entity):
        pass
    
    def train_one(self, userId):
        pass
    
    def load_one(self, userId):
        pass
    
    def save_one(self, userId):
        pass
    
class SPNTurtle(Turtle):
    pass

class DictionaryTurtle(Turtle):

    def __restore__(self):
        super(DictionaryTurtle, self).__restore__()
        self.dictionary = {p.name:p.uid for p in self.pandas}
        
    def generic(self):
        result = super(DictionaryTurtle, self).generic()
        del result['tigress']
        del result['dictionary']
        return result
    
    def _process(self, field):
        return {}
    
    def _get_or_new_panda(self, userId, name):
        if name not in self.dictionary:
            panda = {'monkType':'ExistPanda',
                     'name':name,
                     'creator':userId}
            panda = crane.pandaStore.load_create_by_name(panda, True)
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
            
    def predict(self, userId, entity, fields):
        total = 0
        for field in fields:
            value = translate(getattr(entity, field, ''))
            if not value:
                continue
            
            allTokens = self._process(value)
            entity._raws.update(allTokens)
            entity._features.update([self._get_or_new_panda(userId, t) for t in allTokens])
            total += len(allTokens)

        return total
    
    def aggregate(self, userId):
        # should be taking care of dedups in models and data
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
