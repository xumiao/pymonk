#!/bin/bash

zerorpc --bind tcp://*:4242 
zerorpc --server tcp://127.0.0.1:4242 monk.roles.executor
zerorpc --server tcp://127.0.0.1:4242 monk.roles.executor
