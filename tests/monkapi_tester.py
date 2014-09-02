# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 19:09:12 2014

@author: xm
"""

import monk.core.api as monkapi

class TestMONKAPI:
    TEST_MONK_CONFIG = 'test-monk.yml'
    TEST_TURTLE_SCRIPT = 'test-turtle.yml'
    turtleName = None
    user = 'tester'
    leader = 'monk'
    
    @classmethod
    def setup_class(cls):
        result = monkapi.initialize(cls.TEST_MONK_CONFIG)
        assert result == True
        print "monkapi is initialized --OK"
    
    @classmethod
    def teardown_class(cls):
        result = monkapi.exits()
        assert result == True
        print "monkapi is torn down --OK"
    
    def get_turtle(self):
        if self.turtleName is None:
            turtlep = monkapi.yaml2json(self.TEST_TURTLE_SCRIPT)
            _turtle = monkapi.create_turtle(turtlep)
            self.turtleName = _turtle.name
            self.leader = _turtle.creator
        assert self.turtleName is not None
        return self.turtleName
        
    def test_turtle_creation(self):
        self.get_turtle()
    
    def test_turtle_add_user(self):
        turtleName = self.get_turtle()
        if monkapi.has_turtle_in_store(turtleName, self.user):
            monkapi.remove_turtle(turtleName, self.user)
        result = monkapi.follow_turtle(turtleName, self.user, self.leader)
        assert result != None
        result = monkapi.follow_turtle(turtleName, self.user, self.leader)
        assert result == None
    
    def test_turtle_load_user(self):
        turtleName = self.get_turtle()
        if not monkapi.has_turtle_in_store(turtleName, self.user):
            monkapi.follow_turtle(turtleName, self.user, self.leader)
        result = monkapi.load_turtle(turtleName, self.user)
        assert result != None
        # load can be repeated, overwrite the memory from database
        result = monkapi.load_turtle(turtleName, self.user)
        assert result != None
            
    def test_turtle_remove_user(self):
        turtleName = self.get_turtle()
        if not monkapi.has_turtle_in_store(turtleName, self.user):
            monkapi.follow_turtle(turtleName, self.user, self.leader)
        result = monkapi.remove_turtle(turtleName, self.user)
        assert result == True
        result = monkapi.remove_turtle(turtleName, self.user)
        assert result == False
    
    def test_add_data(self):
        turtleName = self.get_turtle()
        ent = {monkapi.entity.Entity.MONK_TYPE:'Entity',
               monkapi.entity.Entity.FEATURES:[(1,1),(2,2),(3,-1)]}
        if not monkapi.has_turtle_in_store(turtleName, self.user):
            monkapi.follow_turtle(turtleName, self.user, self.leader)
        result = monkapi.add_data(turtleName, self.user, ent)
        assert result == True
        result = monkapi.save_turtle(turtleName, self.user)
        assert result == True

# running nosetests -v <this file> with nose testing framework

# running in command line without nose testing framework
if __name__=='__main__':
    tester = TestMONKAPI()
    tester.setup_class()
    try:
        print 'test_turtle_creation'
        tester.test_turtle_creation()
        print 'test_turtle_add_user'
        tester.test_turtle_add_user()
        print 'test_turtle_load_user'
        tester.test_turtle_load_user()
        print 'test_add_data'
        tester.test_add_data()
    finally:
        tester.teardown_class()
    