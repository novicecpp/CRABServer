#! /bin/bash

set -euo pipefail

printenv
WORKSPACE=$PWD

ssh -i $SSH_KEY -o StrictHostKeyChecking=no crab3@${Environment}.cern.ch "docker exec ${Service} bash -c './stop.sh'; \
docker stop ${Service}; \
docker rm ${Service}; \
~/runContainer_pypi.sh -r registry.cern.ch/cmscrab -v ${Image} -s ${Service}"


#2. check if ${Service} is running
if [ "X${Service}" == "XTaskWorker" ] ; then
	processName=MasterWorker
else
	processName=RunPublisher
fi

ssh -i $SSH_KEY -o StrictHostKeyChecking=no crab3@${Environment}.cern.ch \
"docker exec ${Service} bash -c 'ps exfww | grep $processName | grep -v grep | head -1' || true" > isServiceRunning.log
cat isServiceRunning.log
if [ $(cat isServiceRunning.log |wc -l) -ne 1 ] ; then
	echo "${Service} image in ${Environment} update did not succeed. ${Service} is not running. Please investigate manually." > $WORKSPACE/logFile.txt
	ERR=true
else
	echo "${Service} image in ${Environment} was updated to registry.cern.ch/cmscrab/crabtaskworker:${Image} image tag."  > $WORKSPACE/logFile.txt
    ERR=false
fi


#3. Print running containers
echo -e "\nRunning containers: " >> $WORKSPACE/logFile.txt
ssh -i $SSH_KEY -o StrictHostKeyChecking=no crab3@${Environment}.cern.ch  "docker ps" >> $WORKSPACE/logFile.txt

cat $WORKSPACE/logFile.txt

if [[ "${ERR}" == "true" ]] ; then
	exit 1
fi
