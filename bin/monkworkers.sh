#!/bin/bash
for (( i=0; i < $2; i++ )) 
do
    nohup monkworker $1_$i&
    sleep 1
done
