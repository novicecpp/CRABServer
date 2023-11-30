#! /bin/bash

set -x
#set -euo pipefail

#00. check parameters
echo "(DEBUG) variables from upstream jenkin job:"
echo "(DEBUG)   \- issueTitle: ${issueTitle}"
echo "(DEBUG)   \- Test_Docker_Image: ${Test_Docker_Image}"
echo "(DEBUG)   \- Repo_Testing_Scripts: ${Repo_Testing_Scripts}"
echo "(DEBUG)   \- Branch_Testing_Scripts: ${Branch_Testing_Scripts}"
echo "(DEBUG)   \- Repo_GH_Issue: ${Repo_GH_Issue}"
echo "(DEBUG)   \- Repo_GH_Issue: ${Repo_GH_Issue}"
echo "(DEBUG) end"

#0. Prepare environment
#docker system prune -af
export WORKSPACE=$PWD
mkdir artifacts
ls -l /cvmfs/cms-ib.cern.ch/latest/ 2>&1

#voms-proxy-init -rfc -voms cms -valid 192:00
#export X509_USER_CERT=/home/cmsbld/.globus/usercert.pem
#export X509_USER_KEY=/home/cmsbld/.globus/userkey.pem
#export PROXY=$(voms-proxy-info -path 2>&1)
export PROXY=$X509_USER_PROXY

#git clone https://github.com/cms-sw/cms-bot

export PYTHONPATH=/cvmfs/cms-ib.cern.ch/jenkins-env/python/shared
export ERR=false
#be aware that when running in singularity, we use ${WORK_DIR} set below,
#while if we run in CRAB Docker container, then ${WORK_DIR} set in Dockerfile.
export WORK_DIR=`pwd`
if [[ -z "${Manual_Task_Names}" ]]; then
    cp submitted_tasks $WORKSPACE/artifacts
else
    echo "${Manual_Task_Names}" > $WORKSPACE/artifacts/submitted_tasks
fi

export CMSSW_release_Initial=$CMSSW_release
echo $CMSSW_release_Initial

#1.1. Get configuration from CMSSW_release for master config line
#curl -s -O https://raw.githubusercontent.com/$Repo_Testing_Scripts/$Branch_Testing_Scripts/test/testingConfigs
#CONFIG_LINE=$(grep "master=yes;" testingConfigs)
CONFIG_LINE=$(grep "CMSSW_release=${CMSSW_release};" test/testingConfigs)
export SCRAM_ARCH=$(echo "${CONFIG_LINE}" | tr ';' '\n' | grep SCRAM_ARCH | sed 's|SCRAM_ARCH=||')
export CMSSW_release=$(echo "${CONFIG_LINE}" | tr ';' '\n' | grep CMSSW_release | sed 's|CMSSW_release=||')

echo $SCRAM_ARCH
echo $CMSSW_release

#1.2. Run tests
# dario, 2022-11: why dont we need the singluarity container here?
# stefano, 2023-12: we do not use crab submit here, so do not use
#                   any CMSSW code and are "scram independent"
#export DOCKER_OPT="-u $(id -u):$(id -g) -v /home:/home -v /etc/passwd:/etc/passwd -v /etc/group:/etc/group"
#export DOCKER_ENV="-e inputDataset -e ghprbPullId -e SCRAM_ARCH -e CRABServer_tag -e Client_Validation_Suite -e Task_Submission_Status_Tracking -e Client_Configuration_Validation -e X509_USER_CERT -e X509_USER_KEY -e CMSSW_release -e REST_Instance -e CRABClient_version -e Check_Publication_Status"
#export DOCKER_VOL="-v $WORKSPACE/artifacts/:/data/CRABTesting/artifacts:Z -v /cvmfs/grid.cern.ch/etc/grid-security:/etc/grid-security  -v /cvmfs/grid.cern.ch/etc/grid-security/vomses:/etc/vomses  -v /cvmfs:/cvmfs"
#docker run --rm $DOCKER_OPT $DOCKER_VOL $DOCKER_ENV --net=host \
#$Test_Docker_Image -c 	\
#'source setupCRABClient.sh; ./testingScripts/statusTracking.py' || export ERR=true

source test/container/testingScripts/setupCRABClient.sh;
test/container/testingScripts/statusTracking.py || export ERR=true

#cd ${WORK_DIR}
mv $WORKSPACE/artifacts/* $WORKSPACE/

#export RETRY=${NAGINATOR_COUNT:-0}
#export MAX_RETRY=${NAGINATOR_MAXCOUNT:-4}

export RETRY=${RETRY:-0}
export MAX_RETRY=${MAX_RETRY:-4}


#3. Update issue with submission results
TEST_RESULT='FAILED'
if [ ! -s "./result" ]; then
	MESSAGE='Something went wrong. Investigate manually.'
   	ERR=true
elif grep "TestRunning" result || grep "TestResubmitted" result; then
	if [ $RETRY -ge $MAX_RETRY ] ; then
		MESSAGE='Exceeded configured retries. If needed restart manually.'
    else
    	MESSAGE='Will run again.'
    fi
   	ERR=true
   	TEST_RESULT='FULL-STATUS-UNKNOWN'
elif grep "TestFailed" result ; then
	MESSAGE='Test failed. Investigate manually'
    ERR=true
else
	MESSAGE='Test is done.'
   	TEST_RESULT='SUCCEEDED'
fi

echo -e "**Test:** Task Submission Status Tracking\n\
**Result:** ${TEST_RESULT}\n\
**Attempt:** ${RETRY} out of ${MAX_RETRY}. ${MESSAGE}\n\
**Finished at:** `(date '+%Y-%m-%d %H:%M:%S')`\n\
**Test log:** ${BUILD_URL}console\n" > message_TSResult

echo -e "\`\`\`\n`cat result`\n\`\`\`" >> message_TSResult || true

#$WORKSPACE/cms-bot/create-gh-issue.py -r $Repo_GH_Issue -t "$issueTitle" -R message_TSResult


if $ERR ; then
	exit 1
fi
