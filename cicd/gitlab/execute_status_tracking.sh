#! /bin/bash
if [[ -z "$WORK_DIR" ]]; then
    >&2 echo "Must provide WORK_DIR"
    exit 1
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"
source setupCRABClient.sh;
export PYTHONPATH=/cvmfs/cms.cern.ch/share/cms/crab-prod/v3.231010.00/lib:$PYTHONPATH
python3 statusTracking.py
