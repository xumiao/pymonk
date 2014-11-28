#!/bin/bash
if [ -z ${MONKSOURCE+x} ]; then
    set MONKSOURCE='~/workspace/pymonk'
fi

pushd .
cd $MONKSOURCE
git pull
python setup.py install
popd
