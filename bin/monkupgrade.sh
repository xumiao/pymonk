#!/bin/bash
pushd .
rm -rf $MONKSOURCE
git clone https://github.com/xumiao/pymonk.git $MONKSOURCE
cd $MONKSOURCE
python setup.py install
popd
