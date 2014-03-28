# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 19:09:12 2014

@author: xm
"""

import monk.core.api as monkapi
monkapi.initialize('tests/test-monk.yml')
turtlep = monkapi.yaml2json('tests/test-turtle.yml')
turtle = monkapi.create_turtle(turtlep)
turtle.add_one('xumiao')
turtle.add_one('xumiao')
turtle.load_one('xumiao')
turtle.save_one('xumiao')
ent = monkapi.entity.Entity()
ent[1] = 1
ent[2] = 2
ent[3] = -2
turtle.add_data('xumiao', ent)
turtle.save_one('xumiao')