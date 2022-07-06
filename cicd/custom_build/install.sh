#! /bin/bash
set -euo pipefail

mkdir /tmp/build
cd /tmp/build
git clone $CRABSERVER_REPO -b $CRABSERVER_BRANCH --depth 1
git clone $WMCORE_REPO -b $WMCORE_BRANCH --depth 1
CRAB_INSTALLED_PATH=$(dirname $(dirname $(find /data/srv/ -name RESTBaseAPI.py)))
echo "Install path: $CRAB_INSTALLED_PATH"
rm -rf $CRAB_INSTALLED_PATH/*
cp -r CRABServer/src/python/* $CRAB_INSTALLED_PATH/
cp -r WMCore/src/python/WMCore $CRAB_INSTALLED_PATH/
cp -r WMCore/src/python/Utils $CRAB_INSTALLED_PATH/
chown -R 1000:1000 $CRAB_INSTALLED_PATH/
ls -alh $CRAB_INSTALLED_PATH/
cd -
rm -rf /tmp/build
