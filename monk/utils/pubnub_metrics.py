# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 13:00:41 2014

@author: xumiao
"""

import Pubnub

pubnub_logger = None

def get_pubnub_logger():
    global pubnub_logger
    if pubnub_logger is None:
        pubnub_logger = PubnubLog()
    return pubnub_logger
    
class PubnubLog(object):
    
    def __init__(self):
        self.pubnub = Pubnub.Pubnub(publish_key="pub-c-2be8cb8a-f4b7-45c3-b454-ef13f8f09ae1",
                                    subscribe_key="sub-c-086b6f4e-2325-11e4-934a-02ee2ddab7fe",
                                    ssl_on=False)
        self.channel = "monkmetrics"

    def info(self, message):
        self.pubnub.publish(self.channel, message)
