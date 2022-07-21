#! /bin/bash

set -eo pipefail
set -x
echo "(DEBUG) crabserver image: $CRABSERVER_BASEIMAGE"
echo "(DEBUG) crabserver repo: $CRABSERVER_REPO branch: $CRABSERVER_BRANCH"
echo "(DEBUG) WMCore repo: $WMCORE_REPO branch: $WMCORE_BRANCH"

if [[ -n $CRABSERVER_BASEIMAGE ]]; then
    echo "FROM $CRABSERVER_BASEIMAGE" > Dockerfile2
    sed '1,1d' Dockerfile >> Dockerfile2
    diff -u Dockerfile Dockerfile2 || true # prevent script exit from "set -e"
    mv Dockerfile2 Dockerfile
fi

# default wmcore branch
# FIXME: find from CRABServer/requirements.txt instead
if [[ -z $WMCORE_BRANCH ]]; then
    export WMCORE_BRANCH=2.0.2
fi

set -u

# FIXME: find tag in remote instead clone
git clone $CRABSERVER_REPO -b $CRABSERVER_BRANCH --depth 1
git clone $WMCORE_REPO -b $WMCORE_BRANCH --depth 1
CRABSERVER_HASH=$(cd CRABServer && git rev-parse HEAD | head -c8)
WMCORE_HASH=$(cd WMCore && git rev-parse HEAD | head -c8)
DOCKER_IMAGE_NAMETAG=registry.cern.ch/cmscrab/crabserver:crabserver_$CRABSERVER_HASH.wmcore_$WMCORE_HASH
echo "(DEBUG) new image: $DOCKER_IMAGE_NAMETAG"
docker build \
       -f Dockerfile \
       -t $DOCKER_IMAGE_NAMETAG \
       --build-arg CRABSERVER_REPO=$CRABSERVER_REPO \
       --build-arg CRABSERVER_BRANCH=$CRABSERVER_BRANCH \
       --build-arg WMCORE_REPO=$WMCORE_REPO \
       --build-arg WMCORE_BRANCH=$WMCORE_BRANCH \
       .
export DOCKER_CONFIG=$PWD/docker_login
docker login registry.cern.ch --username $HARBOR_CMSCRAB_USERNAME --password-stdin <<< $HARBOR_CMSCRAB_PASSWORD
docker push $DOCKER_IMAGE_NAMETAG
