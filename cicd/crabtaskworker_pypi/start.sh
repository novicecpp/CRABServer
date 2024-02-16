#!/bin/bash

helpFunction() {
    echo -e "Usage example: ./start.sh -c | -g [-d]"
    echo -e "\t-c start current crabserver instance"
    echo -e "\t-g start crabserver instance from GitHub repo"
    echo -e "\t-d start crabserver in debug mode. Option can be combined with -c or -g"
    exit 1
}

while getopts ":dDcCgGhH" o; do
    case "${o}" in
        h|H) helpFunction ;;
        g|G) MODE="fromGH" ;;
        c|C) MODE="current" ;;
        d|D) DEBUG=true ;;
        * ) echo "Unimplemented option: -$OPTARG"; helpFunction ;;
    esac
done
shift $((OPTIND-1))

if ! [[ -v MODE ]]; then
  echo "Please set how you want to start crabserver (add -c or -g option)." && helpFunction
fi

case $MODE in
    current)
        # current mode: run current instance
        APP_PATH=/data/srv/current/lib/python3.8/site-packages
        ;;
    fromGH)
        # private mode: run private instance from GH
        APP_PATH=/data/repos/CRABServer/src/python
        ./new_updateTMRuntime.sh
        ;;
    *) echo "Unimplemented mode: $MODE\n"; helpFunction ;;
esac

export APP_PATH
export DEBUG
bash -x /data/srv/TaskManager/manage start
