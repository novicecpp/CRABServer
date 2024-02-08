#! /bin/bash

set -x
#set -euo pipefail

#00. check parameters
#echo "(DEBUG) variables from upstream jenkin job:"
#echo "(DEBUG)   \- issueTitle: ${issueTitle}"
#echo "(DEBUG)   \- Test_Docker_Image: ${Test_Docker_Image}"
#echo "(DEBUG)   \- Repo_Testing_Scripts: ${Repo_Testing_Scripts}"
#echo "(DEBUG)   \- Branch_Testing_Scripts: ${Branch_Testing_Scripts}"
#echo "(DEBUG)   \- Repo_GH_Issue: ${Repo_GH_Issue}"
#echo "(DEBUG)   \- Repo_GH_Issue: ${Repo_GH_Issue}"
#echo "(DEBUG) end"

#0. Prepare environment
# root dir can only be the root of crabserver repository
export ROOT_DIR=${ROOT_DIR:-${PWD}}
export WORKSPACE=${WORKSPACE:-testsuite}
#if [[ -d $WORKSPACE ]]; then
#    mv ${WORKSPACE} "${WORKSPACE}_$(printf '%(%Y%m%d_%H%M%S)T\n' -1)"
#fi
mkdir -p $WORKSPACE

pushd $WORKSPACE || exit

#ls -l /cvmfs/cms-ib.cern.ch/latest/ 2>&1

#voms-proxy-init -rfc -voms cms -valid 192:00 || rc=$?
#[[ -n $rc ]] && exit $rc
#export X509_USER_CERT=/home/cmsbld/.globus/usercert.pem
#export X509_USER_KEY=/home/cmsbld/.globus/userkey.pem
#export PROXY=$(voms-proxy-info -path 2>&1)
export X509_USER_PROXY="${X509_USER_PROXY:-/tmp/x509up_u$(id -u)}"
echo "$X509_USER_PROXY"

#git clone https://github.com/cms-sw/cms-bot

#export PYTHONPATH=/cvmfs/cms-ib.cern.ch/jenkins-env/python/shared
export ERR=false
#be aware that when running in singularity, we use ${WORK_DIR} set below,
#while if we run in CRAB Docker container, then ${WORK_DIR} set in Dockerfile.
#export WORK_DIR=`pwd`

# temp create artifacts dir.
# should pass filepath to the script directly (fix statusTracking.py script)
mkdir -p artifacts
if [[ -z "${Manual_Task_Names}" ]]; then
    cp $ROOT_DIR/artifacts/submitted_tasks artifacts
else
    echo "${Manual_Task_Names}" > artifacts/submitted_tasks
fi

#export CMSSW_release_Initial=$CMSSW_release
#echo $CMSSW_release_Initial

#1.1. Get configuration from CMSSW_release for master config line
#curl -s -O https://raw.githubusercontent.com/$Repo_Testing_Scripts/$Branch_Testing_Scripts/test/testingConfigs
#CONFIG_LINE=$(grep "master=yes;" testingConfigs)
#CONFIG_LINE=$(grep "CMSSW_release=${CMSSW_release};" test/testingConfigs)
#export SCRAM_ARCH=$(echo "${CONFIG_LINE}" | tr ';' '\n' | grep SCRAM_ARCH | sed 's|SCRAM_ARCH=||')
#export CMSSW_release=$(echo "${CONFIG_LINE}" | tr ';' '\n' | grep CMSSW_release | sed 's|CMSSW_release=||')

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
export singularity=$(echo ${SCRAM_ARCH} | cut -d"_" -f 1 | tail -c 2)
scramprefix=cc${singularity}
if [ "X${singularity}" == X6 ]; then scramprefix=cc${singularity}; fi
if [ "X${singularity}" == X8 ]; then scramprefix=el${singularity}; fi


/cvmfs/cms.cern.ch/common/cmssw-${scramprefix} -- bash -x $ROOT_DIR/cicd/gitlab/execute_status_tracking.sh $ROOT_DIR || export ERR=true
cp artifacts/result . || true

#cd ${WORK_DIR}
#mv $WORKSPACE/artifacts/* $WORKSPACE/

#export RETRY=${NAGINATOR_COUNT:-0}
#export MAX_RETRY=${NAGINATOR_MAXCOUNT:-4}

#export RETRY=${RETRY:-0}
#export MAX_RETRY=${MAX_RETRY:-4}


#3. Update issue with submission results
TEST_RESULT='FAILED'
if [ ! -s "./result" ]; then
	MESSAGE='Something went wrong. Investigate manually.'
   	ERR=true
elif grep "TestRunning" result || grep "TestResubmitted" result; then
	#if [ $RETRY -ge $MAX_RETRY ] ; then
	#	MESSAGE='Exceeded configured retries. If needed restart manually.'
    #else
    #fi
    MESSAGE='Will run again.'
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
if [[ $TEST_RESULT == 'FULL-STATUS-UNKNOWN' ]]; then
    exit 4
fi
popd
