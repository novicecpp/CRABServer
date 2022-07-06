#! /bin/bash

set -euo pipefail

echo "(DEBUG) crabserver repo: $CRABSERVER_REPO branch: $CRABSERVER_BRANCH"
echo "(DEBUG) WMCore repo: $WMCORE_REPO branch: $WMCORE_BRANCH"
# will hardcode to master when it merged.
git clone https://github.com/novicecpp/CRABServer -b custom_build crabserver_ci
cp -r crabserver_ci/cicd/custom_build/* .
git clone $CRABSERVER_REPO -b $CRABSERVER_BRANCH --depth 1
git clone $WMCORE_REPO -b $WMCORE_BRANCH --depth 1
docker build -f Dockerfile .
