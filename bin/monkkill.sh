#!/bin/bash
for p in `ps aux | pgrep monk$1`
do
	kill -2 $p
done
