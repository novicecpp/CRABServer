#!/bin/bash
<<<<<<< HEAD
# TASKWORKER_HOME only use in this script
TASKWORKER_HOME=/data/srv/TaskManager
CONFIG=$TASKWORKER_HOME/cfg/TaskWorkerConfig.py
# CRABTASKWORKER_ROOT is used to get where data directory is in `DagmanCreator.getLocation()`
export CRABTASKWORKER_ROOT=/data/srv/current/lib/python3.8/site-packages/
# export PYTHONPATH
=======

TASKWORKER_HOME=/data/srv/TaskManager
CONFIG=$TASKWORKER_HOME/cfg/TaskWorkerConfig.py
export CRABTASKWORKER_ROOT=/data/srv/current/lib/python3.8/site-packages/
>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))
export PYTHONPATH=$CRABTASKWORKER_ROOT:$PYTHONPATH
python3 $CRABTASKWORKER_ROOT/TaskWorker/MasterWorker.py --config ${CONFIG} --logDebug &
