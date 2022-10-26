#! /bin/bash
set -euo pipefail
set -x

_tmp=$(find /data/srv/TaskManager/current/ -name DagmanCreator.py)
CRABTW_INSTALL_PATH=${_tmp%/*/*/*}
echo "Install path: $CRABTW_INSTALL_PATH"
rm -rf $CRABTW_INSTALL_PATH/*
cp -r CRABServer/src/python/* $CRABTW_INSTALL_PATH/
cp -r WMCore/src/python/WMCore $CRABTW_INSTALL_PATH/
cp -r WMCore/src/python/Utils $CRABTW_INSTALL_PATH/
cp -r WMCore/src/python/PSetTweaks $CRABTW_INSTALL_PATH/
chown -R 1000:1000 $CRABTW_INSTALL_PATH/
ls -alh $CRABTW_INSTALL_PATH/
# update tw runtime, set GHrepoDir to current dir
export GHrepoDir=$PWD
/data/srv/TaskManager/updateTMRuntime.sh
