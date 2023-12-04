#! /bin/bash
set -x

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "$SCRIPT_DIR"
source setupCRABClient.sh;
export PYTHONPATH=/cvmfs/cms.cern.ch/share/cms/crab-prod/v3.231010.00/lib:$PYTHONPATH
python3 statusTracking.py
popd
