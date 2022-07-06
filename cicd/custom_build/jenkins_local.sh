#! /bin/bash
set -euo pipefail

export CRABSERVER_REPO=https://github.com/novicecpp/CRABServer.git
export CRABSERVER_BRANCH=master
export WMCORE_REPO=https://github.com/dmwm/WMCore.git
export WMCORE_BRANCH=2.0.2
rm -rf ~/playground/jenkins/*
cp -r * ~/playground/jenkins/
( cd ~/playground/jenkins/ && bash ~/playground/jenkins/run.sh )
