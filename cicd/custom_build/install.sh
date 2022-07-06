#! /bin/bash
set -euo pipefail
set -x

export CRAB_INSTALLED_PATH=$(dirname $(dirname $(find /data/srv/ -name RESTBaseAPI.py)))
echo "Install path: $CRAB_INSTALLED_PATH"
rm -rf $CRAB_INSTALLED_PATH/*
cp -r CRABServer/src/python/* $CRAB_INSTALLED_PATH/
cp -r WMCore/src/python/WMCore $CRAB_INSTALLED_PATH/
cp -r WMCore/src/python/Utils $CRAB_INSTALLED_PATH/
chown -R 1000:1000 *
ls -alh
