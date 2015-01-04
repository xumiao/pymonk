#!/bin/bash
pushd .
rm -rf $MONKSOURCE
git clone https://github.com/xumiao/pymonk.git $MONKSOURCE
python setup.py install
popd
