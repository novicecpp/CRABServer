#!/bin/bash

# runContainer.sh: script to pull specified CRAB TW image from defined repo and run it

helpFunction(){
  echo -e "\nUsage example: ./runContainer.sh -v v3.201118 -s TaskWorker"
  echo -e "\t-v TW/Publisher version"
  echo -e "\t-s which service should be started: Publisher, Publisher_schedd, Publisher_asoless, Publisher_rucio or TaskWorker"
  echo -e "\t-r docker hub repo, if not provided, default points to 'cmssw'"
  echo -e "\t-c command that overrides CMD specified in the dockerfile"
  exit 1
  }

while getopts ":v:s:r:h:c:u:" opt
do
    case "$opt" in
      h) helpFunction ;;
      v) TW_VERSION="$OPTARG" ;;
      s) SERVICE="$OPTARG" ;;
      r) TW_REPO="$OPTARG" ;;
      c) COMMAND="$OPTARG" ;;
      u) LOGUUID="$OPTARG" ;;
      :) echo "$0: -$OPTARG needs a value"; helpFunction ;;
      * ) echo "Unimplemented option: -$OPTARG"; helpFunction ;;
    esac
done

if [ -z "${TW_VERSION}" ] || [ -z "${SERVICE}" ]; then
  echo "Make sure to set both -v and -s variables." && helpFunction
fi

#list of directories that should exist on the host machine before container start
dir=("/data/container/${SERVICE}/cfg" "/data/container/${SERVICE}/logs")

case $SERVICE in
  TaskWorker_monit_*)
    DIRECTORY='monit'
    ;;
  TaskWorker*)
    DIRECTORY='TaskManager'
    ;;
  Publisher*)
    DIRECTORY='Publisher'
    dir+=("/data/container/${SERVICE}/PublisherFiles")
    ;;
  *)
    echo "$SERVICE is not a valid service to start. Specify whether you want to start one of the 'Publisher' variants or 'TaskWorker'." && helpFunction
esac

for d in "${dir[@]}"; do
  if ! [ -e "$d" ]; then
    echo "Make sure to create needed directories before starting container. Missing directory: $d" && exit 1
  fi
done

uuid=$(uuidgen)
if [ -n "${LOGUUID}+1" ]; then
    # if LOGUUID is set, then use it
    uuid=${LOGUUID}
fi
tmpfile=/tmp/monit-${uuid}.txt

if [[ "${SERVICE}" == TaskWorker_monit_*  ]]; then
  countrunning=$(docker ps | grep ${SERVICE} | wc -l)
  if [[ ! $countrunning -eq "0" ]]; then
    msg="There already is a running container for $SERVICE. It is likely stuck. Stopping, removing and then starting again."
    echo $msg
    # writing now that the previous execution of the script is hanging.
    # if this execution is ok, then we forget about the previous failure,
    # otherwise we keep track in /tmp/monit-*.txt that we are having problems
    echo $msg > $tmpfile
    docker container stop $SERVICE
  fi
  docker container rm $SERVICE
fi

DOCKER_VOL="-v /data/container/:/data/hostdisk/ -v /data/srv/tmp/:/data/srv/tmp/"
DOCKER_VOL="${DOCKER_VOL} -v /cvmfs/cms.cern.ch:/cvmfs/cms.cern.ch"
DOCKER_VOL="${DOCKER_VOL} -v /etc/grid-security/:/etc/grid-security/"
DOCKER_VOL="${DOCKER_VOL} -v /data/certs/:/data/certs/"
DOCKER_VOL="${DOCKER_VOL} -v /var/run/nscd/socket:/var/run/nscd/socket"
DOCKER_VOL="${DOCKER_VOL} -v /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"
DOCKER_VOL="${DOCKER_VOL} -v /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/etc/pki/tls/certs/ca-bundle.crt"
DOCKER_OPT="-e SERVICE=${SERVICE} -w /data/srv/${DIRECTORY} "

if [[ "${SERVICE}" == TaskWorker_monit_*  ]]; then
  echo "TaskWorker_monit_* detected"
  # # the following two bind mounts are necessary to write to eos. it has been superseded by sending data to opensearch
  # DOCKER_OPT="${DOCKER_OPT} -v /eos/project-c/cmsweb/www/CRAB/:/data/eos "
  # DOCKER_OPT="${DOCKER_OPT} -v /tmp/krb5cc_1000:/tmp/krb5cc_1000 "

  # - monit script does not work with `-di` option inside crontab. 
  # - in order to get the exit code of the command run inside docker container, 
  #   remove the `-d` option for monit crontabs
else
  # start docker container in background when you run TW and Published, not monitoring scripts.
  DOCKER_OPT="${DOCKER_OPT} -d"
fi

docker run --name ${SERVICE} -t --net host --privileged $DOCKER_OPT $DOCKER_VOL ${TW_REPO:-registry.cern.ch/cmscrab}/crabtaskworker:${TW_VERSION} $COMMAND > $tmpfile
if [ $? -eq 0 ]; then
  # if the crontab does not fail, remove the log file
  rm $tmpfile
fi

echo -e "Sleeping for 3 seconds.\nRunning containers:"
sleep 3 && docker ps
