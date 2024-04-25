#! /bin/bash

# Same style as crabserver_pypi/manage.sh script, but for crabtaskworker.
# This script needs following environment variables:
#   - DEBUG:   if `true`, setup debug mode environment.
#   - PYTHONPATH: inherit from ./start.sh

##H Usage: manage.sh ACTION [ATTRIBUTE] [SECURITY-STRING]
##H
##H Available actions:
##H   help        show this help
##H   version     get current version of the service
##H   restart     (re)start the service
##H   start       (re)start the service
##H   stop        stop the service

set -euo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

## some variable use in start_srv
CONFIG="${SCRIPT_DIR}"/cfg/TaskWorkerConfig.py

# Inherit PYTHONPATH from ./start.sh
PYTHONPATH=${PYTHONPATH:-/data/srv/current/lib/python/site-packages}
export PYTHONPATH

usage()
{
    cat $0 | grep "^##H" | sed -e "s,##H,,g"
}

start_srv() {
    if [[ "$DEBUG" == true ]]; then
        APP_DIR=${APP_DIR:-/data/repos/CRABServer/src/python}
        python3 ${APP_DIR}/Publisher/RunPublisher.py --config ${CONFIG} --service ${SERVICE} --debug --testMode
    else
        APP_DIR=/data/srv/current/lib/python/site-packages
        python3 ${APP_DIR}/Publisher/RunPublisher.py --config ${CONFIG} --service ${SERVICE} | tee stdout.txt &
    fi
}

stop_srv() {
    # This part is copy from https://github.com/dmwm/CRABServer/blob/3af9d658271a101db02194f48c5cecaf5fab7725/src/script/Deployment/TaskWorker/stop.sh
    # TW is given checkTimes*timeout seconds to stop, if it is still running after
    # this period, TW and all its slaves are killed by sending SIGKILL signal.

  # find my bearings
  thisScript=`realpath $0`
  myDir=`dirname ${thisScript}`
  myLog=${myDir}/logs/log.txt

  PublisherBusy(){
  # a function to tell if PublisherMaster is busy or waiting
  #   return 0 = success = Publisher is Busy
  #   return 1 = failure = Publisher can be killed w/o fear
    lastLine=`tail -1 ${myLog}`
    echo ${lastLine}|grep -q 'Next cycle will start at'
    cycleDone=$?
    if [ $cycleDone = 1 ] ; then
      # inside working cycle
      return 0
    else
      # in waiting mode, checks when it is next start
      start=`echo $lastLine|awk '{print $NF}'`
      startTime=`date -d ${start} +%s`  # in seconds from Epoch
      now=`date +%s` # in seconds from Epoch
      delta=$((${startTime}-${now}))
      if [ $delta -gt 60 ]; then
        # no race with starting of next cycle, safe to kill
        return 1
      else
        # next cycle about to start, wait until is done
        return 0
      fi
    fi
  }

  nIter=1
  while PublisherBusy
  do
    [ $nIter = 1 ] && echo "Waiting for MasterPublisher to complete cycle: ."
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
  pkill -f RunPublisher

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
    usage
    ;;

  * )
    echo "$0: unknown action '$1', please try '$0 help' or documentation." 1>&2
    exit 1
    ;;
esac