#! /bin/bash

cd "$(git rev-parse --show-toplevel)"
source test/container/testingScripts/setupCRABClient.sh;
export PYTHONPATH=/cvmfs/cms.cern.ch/share/cms/crab-prod/v3.231010.00/lib:$PYTHONPATH
python3 ./test/container/testingScripts/statusTracking.py
