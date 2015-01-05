#!/bin/bash
for (( i=0; i <= $2; i++ )) 
do
    monkworker $1_$i
done
