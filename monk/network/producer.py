# -*- coding: utf-8 -*-
"""
Created on Sun Nov 16 11:34:27 2014

@author: xm
"""

from __future__ import absolute_import
import logging
from kafka.producer.base import Producer, BATCH_SEND_DEFAULT_INTERVAL, BATCH_SEND_MSG_COUNT
from monk.network.partitioner import UserPartitioner

logger = logging.getLogger("monk.network.producer")

class FixedProducer(Producer):
    """
        A simple, fixed partition producer. Each message goes to exactly the same partition
        Params:
            client - The Kafka client instance to use
            partition - The partition number to fix on
            async - If True, the messages are sent asynchronously via another
                    thread (process). We will not wait for a response to these
            req_acks - A value indicating the acknowledgements that the server must
                    receive before responding to the request
            ack_timeout - Value (in milliseconds) indicating a timeout for waiting
                    for an acknowledgement
            batch_send - If True, messages are send in batches
            batch_send_every_n - If set, messages are send in batches of this size
            batch_send_every_t - If set, messages are send after this timeout
    """
    def __init__(self, client, partition, async=False, req_acks=Producer.ACK_AFTER_LOCAL_WRITE, ack_timeout=Producer.DEFAULT_ACK_TIMEOUT,
             codec=None, batch_send=False, batch_send_every_n=BATCH_SEND_MSG_COUNT, batch_send_every_t=BATCH_SEND_DEFAULT_INTERVAL):
        #TODO: check the range of partition
        self.partition = partition
        super(FixedProducer, self).__init__(client, async, req_acks, ack_timeout, codec, batch_send, batch_send_every_n, batch_send_every_t)
        
    def send(self, topic, name, *msg):
        logger.info('sending message {} at {}@{}'.format(msg, topic, self.partition))
        return self.send_messages(topic, self.partition, *msg)
    
    def __repr__(self):
        return '<FixedProducer batch=%s>' % self.async
        
class UserProducer(Producer):
    """
        A user partitioned producer. Each message goes to the partition decided according to the user
        Params:
            client - The Kafka client instance to use
            async - If True, the messages are sent asynchronously via another
                    thread (process). We will not wait for a response to these
            req_acks - A value indicating the acknowledgements that the server must
                    receive before responding to the request
            ack_timeout - Value (in milliseconds) indicating a timeout for waiting
                    for an acknowledgement
            batch_send - If True, messages are send in batches
            batch_send_every_n - If set, messages are send in batches of this size
            batch_send_every_t - If set, messages are send after this timeout
    """
    def __init__(self, client, async=False, req_acks=Producer.ACK_AFTER_LOCAL_WRITE, ack_timeout=Producer.DEFAULT_ACK_TIMEOUT,
             codec=None, batch_send=False, batch_send_every_n=BATCH_SEND_MSG_COUNT, batch_send_every_t=BATCH_SEND_DEFAULT_INTERVAL):
        self.partitioner = UserPartitioner(None)
        super(UserProducer, self).__init__(client, async, req_acks, ack_timeout, codec, batch_send, batch_send_every_n, batch_send_every_t)
        
    def send(self, topic, name, *msg):
        partition = self.partitioner.partition(name, None)
        logger.info('sending message {} at {}@{}'.format(msg, topic, partition))
        return self.send_messages(topic, partition, *msg)
    
    def __repr__(self):
        return '<UserProducer batch=%s>' % self.async
    