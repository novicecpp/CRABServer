#!/bin/bash

TASKWORKER_HOME=/data/srv/TaskManager
#export CRABTASKWORKER_ROOT=$TASKWORKER_HOME/CRABServer

export PYTHONPATH=$TASKWORKER_HOME/current/lib/python3.8/site-packages/:$PYTHONPATH
CONFIG=$TASKWORKER_HOME/cfg/TaskWorkerConfig.py
export CRABTASKWORKER_ROOT=$TASKWORKER_HOME/current
python3 $TASKWORKER_HOME/current/lib/python3.8/site-packages/TaskWorker/MasterWorker.py --config ${CONFIG} --logDebug &
