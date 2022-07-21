#! /bin/bash
set -eo pipefail

# jenkins parameter
export CRABSERVER_BASEIMAGE=registry.cern.ch/cmsweb/crabserver:v3.220713
export CRABSERVER_REPO=https://github.com/novicecpp/CRABServer.git
export CRABSERVER_BRANCH=revert_s3_force_ipv4
export WMCORE_REPO=https://github.com/dmwm/WMCore.git
export WMCORE_BRANCH=2.0.2
# expect harbor username/password
if [[ -z $HARBOR_CMSCRAB_USERNAME ]]; then
   >&2 echo "require env HARBOR_CMSCRAB_USERNAME/HARBOR_CMSCRAB_PASSWORD"
   exit 1
fi
# for local run
rm -rf ~/playground/jenkins/*
cp -r * ~/playground/jenkins/
( cd ~/playground/jenkins/ && bash run.sh )
