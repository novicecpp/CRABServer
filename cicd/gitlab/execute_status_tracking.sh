#! /bin/bash
set -x

ROOT_DIR=${1}
echo "Working direcotry: $WORKSPACE"
source $ROOT_DIR/cicd/gitlab/setupCRABClient.sh;
export WORK_DIR=.
python3 $ROOT_DIR/cicd/gitlab/statusTracking.py
