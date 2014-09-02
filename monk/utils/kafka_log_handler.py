# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 10:17:24 2014

@author: xumiao
"""

from kafka.client import KafkaClient
from kafka.producer import KeyedProducer
import logging,sys

class KafkaLoggingHandler(logging.Handler):

    def __init__(self, hosts='', topic='', partition=0):
        logging.Handler.__init__(self)
        self.kafkaClient = KafkaClient(hosts)
        self.topic = topic
        self.partition = partition
        self.producer = KeyedProducer(self.kafkaClient, async=False,
                                      req_acks=KeyedProducer.ACK_AFTER_LOCAL_WRITE,
                                      ack_timeout=200)

    def emit(self, record):
        #drop kafka logging to avoid infinite recursion
        if record.name == 'kafka':
            return
        try:
            #use default formatting
            msg = self.format(record)
            #produce message
            self.producer.send_messages(self.topic + record.name, self.partition, msg)
        except:
            import traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei

    def close(self):
        self.producer.stop()
        logging.Handler.close(self)
