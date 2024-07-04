#! /bin/bash

# Start the Publisher service.

##H Usage: manage.sh ACTION
##H
##H Available actions:
##H   help        show this help
##H   version     get current version of the service
##H   restart     (re)start the service
##H   start       (re)start the service
##H   stop        stop the service
##H
##H This script needs following environment variables for start action:
##H   - DEBUG:      if `true`, setup debug mode environment.
##H   - PYTHONPATH: inherit from ./start.sh
##H   - SERVICE:    inherit from container environment
##H                 (e.g., `-e SERVICE=Publisher_schedd` when do `docker run`)

set -euo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
if [[ -n ${TRACE+x} ]]; then
    set -x
    export TRACE
fi

# some variable use in start_srv
CONFIG="${SCRIPT_DIR}"/current/PublisherConfig.py
PROCESS_NAME=RunPublisher.py

helpFunction() {
    grep "^##H" "${0}" | sed -r "s/##H(| )//g"
}

_getRunPublisherPid() {
    pid=$(pgrep -f "${PROCESS_NAME}" | grep -v grep | head -1 ) || true
    echo "${pid}"
}

_isPublisherBusy() {
    # a function to tell if PublisherMaster is busy or waiting
    #   return 0 = success = Publisher is Busy
    #   return 1 = failure = Publisher can be killed w/o fear
    # Check if Publisher process is still running
    # find my bearings
    myLog="${SCRIPT_DIR}"/hostdisk/logs/log.txt
    if [[ ! -f "$myLog" ]]; then
        echo "Error: \"${myLog}\" could not be found."
        exit 1
    fi

    # check if it still running
    [[ -z "$(_getRunPublisherPid)" ]] && return 1

    lastLine=$(tail -1 "${myLog}")
    echo "${lastLine}" | grep -q 'Next cycle will start at'
    cycleDone=$?
    if [[ $cycleDone = 1 ]] ; then
        # inside working cycle
        return 0
    else
        # in waiting mode, checks when it is next start
        start=$(echo "${lastLine}" | awk '{print $NF}')
        startTime=$(date -d ${start} +%s)  # in seconds from Epoch
        now=$(date +%s) # in seconds from Epoch
        delta=$((${startTime}-${now}))
        if [[ $delta -gt 60 ]]; then
            # no race with starting of next cycle, safe to kill
            return 1
        else
            # next cycle about to start, wait until is done
            return 0
        fi
    fi
}

start_srv() {
    echo "Starting Publisher..."
    # Check require env
    # shellcheck disable=SC2269
    SERVICE="${SERVICE}"
    # shellcheck disable=SC2269
    DEBUG="${DEBUG}"
    export PYTHONPATH="${PYTHONPATH}"

    # hardcode APP_DIR, but if debug mode, APP_DIR can be override
    if [[ "${DEBUG}" = 'true' ]]; then
        APP_DIR="${APP_DIR:-/data/repos/CRABServer/src/python}"
        python3 "${APP_DIR}"/Publisher/RunPublisher.py --config "${CONFIG}" --service "${SERVICE}" --debug --testMode
    else
        APP_DIR=/data/srv/current/lib/python/site-packages
        python3 "${APP_DIR}"/Publisher/RunPublisher.py --config "${CONFIG}" --service "${SERVICE}" &
    fi
}

stop_srv() {
    echo "Stopping Publisher..."
    if [[ -z "$(_getRunPublisherPid)" ]]; then
        echo "No Publisher is running."
        return 0
    fi

    nIter=1
    while _isPublisherBusy
    do
        [[ $nIter = 1 ]] && echo "Waiting for MasterPublisher to complete cycle: ."
        nIter=$((nIter+1))
        sleep 10
        echo -n "."
        if (( nIter%6  == 0 )); then
            minutes=$((nIter/6))
            echo -n "${minutes}m"
        fi
    done
    echo ""
    echo "Publisher is in waiting now. Killing RunPublisher"
    # ignore retcode in case it got kill by other process or crash
    pkill -f "${PROCESS_NAME}" || true
}

# Main routine, perform action requested on command line.
case ${1:-help} in
  start | restart )
    stop_srv
    start_srv
    ;;

  stop )
    stop_srv
    ;;

  help )
    helpFunction
    exit 0
    ;;

  * )
    echo "$0: unknown action '$1', please try '$0 help' or documentation." 1>&2
    exit 1
    ;;
esac
