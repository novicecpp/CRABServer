#! /bin/bash
set -euo pipefail

CRABSERVER_INSTALLED_PATH=$(dirname $(dirname $(find /data/srv/ -name RESTBaseAPI.py)))
echo "Install path: $CRABSERVER_INSTALLED_PATH"
rm -rf $CRABSERVER_INSTALLED_PATH/*
cp -r CRABServer/src/python/* $CRABSERVER_INSTALLED_PATH/
cp -r WMCore/src/python/WMCore $CRABSERVER_INSTALLED_PATH/
cp -r WMCore/src/python/Utils $CRABSERVER_INSTALLED_PATH/
chown -R 1000:1000 $CRABSERVER_INSTALLED_PATH/
ls -alh $CRABSERVER_INSTALLED_PATH/
