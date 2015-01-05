#!/bin/bash
for (( i=0; i<=$2; i++ )) 
do
    monkadmin $1.$i
done
