#!/bin/bash

set -euo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "${SCRIPT_DIR}"
rm -rf dmwm
git clone --depth 1 https://gitlab.cern.ch/CMSDOCKS/dmwm -b master
pushd dmwm/crab_staticanalysis
docker build --push -t registry.cern.ch/cmscrab/crab_staticanalysis:${IMAGE_TAG:-v3.latest} .
