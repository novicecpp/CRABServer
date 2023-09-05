#! /bin/bash
set -eo pipefail

# manually change these value
CRABSERVER_REPO=https://github.com/novicecpp/CRABServer.git
#CRABSERVER_BRANCH=rucio_transfers_store_transfer_info_in_tasks_db
#CRABSERVER_BRANCH=revert_expand_sandbox
CRABSERVER_BRANCH=rucio_transfers_master_fix_rebase
WMCORE_REPO=https://github.com/dmwm/WMCore.git
WMCORE_BRANCH=2.1.8
CRABSERVER_BASEIMAGE=registry.cern.ch/cmsweb/crabserver:v3.230824.1
CRABTASKWORKER_BASEIMAGE=registry.cern.ch/cmscrab/crabtaskworker:v3.230824.1

# export parameter for subshell
export CRABSERVER_REPO \
       CRABSERVER_BRANCH \
       WMCORE_REPO WMCORE_BRANCH \
       CRABSERVER_BASEIMAGE \
       CRABTASKWORKER_BASEIMAGE

# expect harbor username/password
if [[ -z $HARBOR_CMSCRAB_USERNAME ]]; then
   >&2 echo "require env HARBOR_CMSCRAB_USERNAME/HARBOR_CMSCRAB_PASSWORD"
   exit 1
fi
# for local run
mkdir -p ~/playground/jenkins/
rm -rf ~/playground/jenkins/*
cp -r ./* ~/playground/jenkins/
( cd ~/playground/jenkins/ && bash run.sh )
