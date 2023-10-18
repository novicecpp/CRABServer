#!/bin/bash

TASKWORKER_HOME=/data/srv/TaskManager
CONFIG=$TASKWORKER_HOME/cfg/TaskWorkerConfig.py
export CRABTASKWORKER_ROOT=/data/srv/current/lib/python3.8/site-packages/
export PYTHONPATH=$CRABTASKWORKER_ROOT:$PYTHONPATH
python3 $CRABTASKWORKER_ROOT/TaskWorker/MasterWorker.py --config ${CONFIG} --logDebug &
