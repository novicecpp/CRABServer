#! /bin/bash

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

if [[ "${DEBUG}" == true ]]; then
  # this will direct WMCore/REST/Main.py to run in the foreground rather than as a demon
  # allowing among other things to insert pdb calls in the crabserver code and debug interactively
  export DONT_DAEMONIZE_REST=True
  # this will start crabserver with only one thread (default is 25) to make it easier to run pdb
  export CRABSERVER_THREAD_POOL=1
fi

if [[ "${MODE}" == fromGH ]]; then
    export PYTHONPATH=/data/repos/CRABServer/src/python:/data/repos/WMCore/src/python/:${PYTHONPATH}
fi
/data/manage start
