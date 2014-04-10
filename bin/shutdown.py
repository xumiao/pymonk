# -*- coding: utf-8 -*-
"""
Created on Wed Apr 09 17:24:06 2014

@author: xumiao
"""

from kafka.client import KafkaClient
from kafka.producer import BroadcastProducer
import sys
import getopt

def print_help():
    print 'shutdown.py -k <host:port> -t <topic>'
    
def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hk:t:',['kafka=','topic='])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    kafkaHost = None
    topic = None
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ('-k', '--kafka'):
            kafkaHost = arg
        elif opt in ('-t', '--topic'):
            topic = arg
    
    if not kafkaHost or not topic:
        print_help()
        sys.exit()
        
    kafka = KafkaClient(kafkaHost)
    producer = BroadcastProducer(kafka, topic, async=False,
                          req_acks=BroadcastProducer.ACK_AFTER_LOCAL_WRITE,
                          ack_timeout=2000)
    producer.send('{"operation":"shutdown"}')
    
if __name__=='__main__':
    main(sys.argv[1:])