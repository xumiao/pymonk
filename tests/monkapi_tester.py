# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 19:09:12 2014

@author: xm
"""

import monk.core.api as monkapi

class TestMONKAPI:
    TEST_MONK_CONFIG = 'test-monk.yml'
    TEST_TURTLE_SCRIPT = 'test-turtle.yml'
    USER_ID = 'tester'
    turtle_id = None
    
    @classmethod
    def setup_class(cls):
        result = monkapi.initialize(cls.TEST_MONK_CONFIG)
        assert result == True
        print "monkapi is initialized --OK"
    
    @classmethod
    def teardown_class(cls):
        result = monkapi.exit()
        assert result == True
        print "monkapi is torn down --OK"
    
    def get_turtle(self):
        if self.turtle_id is None:
            turtlep = monkapi.yaml2json(self.TEST_TURTLE_SCRIPT)
            self.turtle_id = monkapi.find_turtle(turtlep)
        assert self.turtle_id is not None
        return self.turtle_id
        
    def test_turtle_creation(self):
        self.get_turtle()
    
    def test_turtle_add_partition(self):
        turtle_id = self.get_turtle()
        if monkapi.has_one_in_store(turtle_id, self.USER_ID):
            monkapi.remove_one(turtle_id, self.USER_ID)
        result = monkapi.add_one(turtle_id, self.USER_ID)
        assert result == True
        result = monkapi.add_one(turtle_id, self.USER_ID)
        assert result == False
    
    def test_turtle_load_partition(self):
        turtle_id = self.get_turtle()
        if not monkapi.has_one_in_store(turtle_id, self.USER_ID):
            monkapi.add_one(turtle_id, self.USER_ID)
        if monkapi.has_one(turtle_id, self.USER_ID):
            monkapi.unload_one(turtle_id, self.USER_ID)
        result = monkapi.load_one(turtle_id, self.USER_ID)
        assert result == True
        # load can be repeated, overwrite the memory from database
        result = monkapi.load_one(turtle_id, self.USER_ID)
        assert result == True
            
    def test_turtle_remove_partition(self):
        turtle_id = self.get_turtle()
        if not monkapi.has_one_in_store(turtle_id, self.USER_ID):
            monkapi.add_one(turtle_id, self.USER_ID)
        result = monkapi.remove_one(turtle_id, self.USER_ID)
        assert result == True
        result = monkapi.remove_one(turtle_id, self.USER_ID)
        assert result == False
    
    def test_turtle_unload_partition(self):
        turtle_id = self.get_turtle()
        if not monkapi.has_one_in_store(turtle_id, self.USER_ID):
            monkapi.add_one(turtle_id, self.USER_ID)
        if not monkapi.has_one(turtle_id, self.USER_ID):
            monkapi.load_one(turtle_id, self.USER_ID)
        result = monkapi.unload_one(turtle_id, self.USER_ID)
        assert result == True
        result = monkapi.unload_one(turtle_id, self.USER_ID)
        assert result == False

    def test_turtle_save_partition(self):
        turtle_id = self.get_turtle()
        if monkapi.has_one_in_store(turtle_id, self.USER_ID):
            monkapi.remove_one(turtle_id, self.USER_ID)
        result = monkapi.save_one(turtle_id, self.USER_ID)
        assert result == False
        monkapi.add_one(turtle_id, self.USER_ID)
        result = monkapi.save_one(turtle_id, self.USER_ID)
        assert result == True
        monkapi.unload_one(turtle_id, self.USER_ID)
        result = monkapi.save_one(turtle_id, self.USER_ID)
        assert result == False

    def test_add_data(self):
        turtle_id = self.get_turtle()
        ent = monkapi.entity.Entity()
        ent[1] = 1
        ent[2] = 2
        ent[3] = -1
        monkapi.add_one(turtle_id, self.USER_ID)
        result = monkapi.add_data(turtle_id, self.USER_ID, ent)
        assert result == True
        result = monkapi.save_one(turtle_id, self.USER_ID)
        assert result == True

# running nosetests -v <this file> with nose testing framework

# running in command line without nose testing framework
if __name__=='__main__':
    tester = TestMONKAPI()
    tester.setup_class()
    try:
        tester.test_turtle_creation()
        tester.test_turtle_add_partition()
        tester.test_turtle_load_partition()
    finally:
        tester.teardown_class()
    