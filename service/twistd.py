# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 15:31:56 2013

@author: xumiao
"""

#!C:\aroot\stage\python.exe
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
import os, sys

try:
    import _preamble
except ImportError:
    sys.exc_clear()

sys.path.insert(0, os.path.abspath(os.getcwd()))

from twisted.scripts.twistd import run
run()
