# -*- coding: utf-8 -*-
"""
Created on Sat Feb 01 10:45:09 2014
Training models remotely in cloud
@author: pacif_000
"""

from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
import os
import platform
if platform.system() == 'Windows':
    import win32api
else:
    import signal
import thread
import traceback

kafkaHost = 'monkkafka.cloudapp.net:9092,monkkafka.cloudapp.net:9093,monkkafka.cloudapp.net:9094'
kafkaTopic = 'expr'
kafkaGroup = 'expr'

kafka = None
producer = None
consumer = None

def onexit():
    global kafka, consumer, producer
    if consumer:
        consumer.commit()
        consumer.stop()
        consumer = None
    if producer:
        producer.stop()
        producer = None
    if kafka:
        kafka.close()
        kafka = None
    print('remote_rainter {0} is shutting down'.format(os.getpid()))

def handler(sig, hook = thread.interrupt_main):
    global kafka, consumer, producer
    if consumer:
        consumer.commit()
        consumer.stop()
        consumer = None
    if producer:
        producer.stop()
        producer = None
    if kafka:
        kafka.close()
        kafka = None
    print('remote_rainter {0} is shutting down'.format(os.getpid()))
    exit(1)
    
def server():
    global kafka, producer, consumer
    if platform.system() == 'Windows':
        win32api.SetConsoleCtrlHandler(handler, 1)
    else:
        signal.signal(signal.SIGINT, onexit)
    
    try:
        kafka = KafkaClient(kafkaHost,timeout=None)
        consumer = SimpleConsumer(kafka, kafkaGroup, kafkaTopic, partitions=[0,1,2])

        for message in consumer:
            print(message)
    except Exception as e:
        print('Exception {0}'.format(e))
        print('Can not consume actions')
        print(traceback.format_exc())
    except KeyboardInterrupt:
        onexit()
    finally:
        onexit()

if __name__=='__main__':
    while 1:
        server()
