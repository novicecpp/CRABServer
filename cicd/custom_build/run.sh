#! /bin/bash

set -eo pipefail
set -x
echo "(DEBUG) crabserver image: $CRABSERVER_BASEIMAGE"
echo "(DEBUG) crabserver repo: $CRABSERVER_REPO branch: $CRABSERVER_BRANCH"
echo "(DEBUG) WMCore repo: $WMCORE_REPO branch: $WMCORE_BRANCH"

if [[ -n $CRABSERVER_BASEIMAGE ]]; then
    echo "FROM $CRABSERVER_BASEIMAGE" > crabserver/Dockerfile2
    sed '1,1d' crabserver/Dockerfile >> crabserver/Dockerfile2
    diff -u crabserver/Dockerfile crabserver/Dockerfile2 || true # prevent script exit from "set -e"
    mv crabserver/Dockerfile2 crabserver/Dockerfile
fi

if [[ -n $CRABTASKWORKER_BASEIMAGE ]]; then
    echo "FROM $CRABTASKWORKER_BASEIMAGE" > crabtaskworker/Dockerfile2
    sed '1,1d' crabtaskworker/Dockerfile >> crabtaskworker/Dockerfile2
    diff -u crabtaskworker/Dockerfile crabtaskworker/Dockerfile2 || true # prevent script exit from "set -e"
    mv crabtaskworker/Dockerfile2 crabtaskworker/Dockerfile
fi

# default wmcore branch
# FIXME: find from CRABServer/requirements.txt instead
if [[ -z $WMCORE_BRANCH ]]; then
    export WMCORE_BRANCH=2.0.2
fi

set -u

# FIXME: find tag in remote instead clone
mkdir latest
git clone $CRABSERVER_REPO -b $CRABSERVER_BRANCH --depth 1 latest/CRABServer
git clone $WMCORE_REPO -b $WMCORE_BRANCH --depth 1 latest/WMCore
CRABSERVER_HASH=$(cd latest/CRABServer && git rev-parse HEAD | head -c8)
WMCORE_HASH=$(cd latest/WMCore && git rev-parse HEAD | head -c8)
TAG=crabserver_$CRABSERVER_HASH.wmcore_$WMCORE_HASH
CRABSERVER_NAMETAG=registry.cern.ch/cmsweb/crabserver:$TAG
CRABTASKWORKER_NAMETAG=registry.cern.ch/cmscrab/crabtaskworker:$TAG
echo "(DEBUG) new CRABServer tag: $CRABSERVER_NAMETAG"
echo "(DEBUG) new TaskWorker tag: $CRABTASKWORKER_NAMETAG"

docker build \
       -f crabserver/Dockerfile \
       -t $CRABSERVER_NAMETAG \
       .

docker build \
       -f crabtaskworker/Dockerfile \
       -t $CRABTASKWORKER_NAMETAG \
       .

export DOCKER_CONFIG=$PWD/docker_login
docker login registry.cern.ch --username $HARBOR_CMSCRAB_USERNAME --password-stdin <<< $HARBOR_CMSCRAB_PASSWORD
docker push $CRABSERVER_NAMETAG
docker push $CRABTASKWORKER_NAMETAG

echo "deploy with this command:"
echo "kubectl set image deployment/crabserver crabserver=registry.cern.ch/cmsweb/crabserver:$TAG"
echo "ssh crab-dev-tw03 \"sudo -u crab3 bash -c 'cd ~; docker rm -f TaskWorker && ./runContainer.sh -s TaskWorker -v $TAG'\""
