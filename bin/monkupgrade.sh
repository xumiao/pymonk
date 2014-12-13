#!/bin/bash
pushd .
cd $MONKSOURCE
git pull
python setup.py install
popd
