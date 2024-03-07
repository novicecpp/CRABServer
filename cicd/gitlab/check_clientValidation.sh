#! /bin/bash

set -euo pipefail

#00. check parameters
echo "(DEBUG) variables from upstream jenkin job:"
echo "(DEBUG)   \- SCRAM_ARCH: ${SCRAM_ARCH}"
echo "(DEBUG)   \- singularity: ${singularity}"
echo "(DEBUG)   \- CMSSW_release: ${CMSSW_release}"
#echo "(DEBUG)   \- issueTitle: ${issueTitle}"
#echo "(DEBUG)   \- Test_Docker_Image: ${Test_Docker_Image}"
#echo "(DEBUG)   \- Repo_Testing_Scripts: ${Repo_Testing_Scripts}"
#echo "(DEBUG)   \- Branch_Testing_Scripts: ${Branch_Testing_Scripts}"
#echo "(DEBUG)   \- Repo_GH_Issue: ${Repo_GH_Issue}"
echo "(DEBUG) end"

SUBMITTED_TASKS_PATH=artifacts/submitted_tasks_CV_${CMSSW_release}
cat $SUBMITTED_TASKS_PATH
export SUBMITTED_TASKS_PATH

# need these steps to make client read proxyfile properly
cp $X509_USER_PROXY proxyfile
chmod 0600 proxyfile
chown $(id -u):$(id -g) proxyfile
export X509_USER_PROXY="$(realpath proxyfile)"
export X509_USER_CERT=$X509_USER_PROXY
export X509_USER_KEY=$X509_USER_PROXY

#0. Prepare environment
#docker system prune -af
#mkdir artifacts
#ls -l /cvmfs/cms-ib.cern.ch/latest/ 2>&1
#
#export X509_USER_CERT=/home/cmsbld/.globus/usercert.pem
#export X509_USER_KEY=/home/cmsbld/.globus/userkey.pem

#git clone https://github.com/cms-sw/cms-bot

#export ERR=false
#export singularity=$singularity
#cp submitted_tasks $WORKSPACE/artifacts

export WORK_DIR=workdir
mkdir -p $WORK_DIR

#1. Start tests
if [ "X${singularity}" == X6 ] || [ "X${singularity}" == X7 ] || [ "X${singularity}" == X8 ] ; then
	#voms-proxy-init -rfc -voms cms -valid 192:00
	#export PROXY=$(voms-proxy-info -path 2>&1)
	echo "Starting singularity ${singularity} container."
    #git clone https://github.com/$Repo_Testing_Scripts
    #pushd test/container/testingScripts
    #git checkout $Branch_Testing_Scripts
    if [ "X${singularity}" == X6 ] ; then export TEST_LIST=SL6_TESTS; fi
    if [ "X${singularity}" == X7 ] ; then export TEST_LIST=FULL_TEST; fi
    if [ "X${singularity}" == X8 ] ; then export TEST_LIST=FULL_TEST; fi
    cp $SUBMITTED_TASKS_PATH $WORK_DIR
    scramprefix=cc${singularity}
    if [ "X${singularity}" == X6 ]; then scramprefix=cc${singularity}; fi
    if [ "X${singularity}" == X7 ]; then scramprefix=cc${singularity}; fi
    if [ "X${singularity}" == X8 ]; then scramprefix=el${singularity}; fi
	/cvmfs/cms.cern.ch/common/cmssw-${scramprefix} -- cicd/gitlab/clientValidation.sh || export ERR=true
	#mv client-validation.log $WORKSPACE/ || true
#SB elif [ "X${singularity}" == X7 ]; then
#SB 	export TEST_LIST=FULL_TEST
#SB 	export DOCKER_OPT="-u $(id -u):$(id -g) -v /home:/home -v /etc/passwd:/etc/passwd -v /etc/group:/etc/group"
#SB 	export DOCKER_ENV="-e TEST_LIST -e inputDataset -e ghprbPullId -e SCRAM_ARCH -e CRABServer_tag -e Client_Validation_Suite -e Task_Submission_Status_Tracking -e Client_Configuration_Validation -e X509_USER_CERT -e X509_USER_KEY -e CMSSW_release -e REST_Instance -e CRABClient_version"
#SB 	export DOCKER_VOL="-v $WORKSPACE/artifacts/:/data/CRABTesting/artifacts:Z -v /cvmfs/grid.cern.ch/etc/grid-security:/etc/grid-security  -v /cvmfs/grid.cern.ch/etc/grid-security/vomses:/etc/vomses  -v /cvmfs:/cvmfs"
#SB 	docker run --rm $DOCKER_OPT $DOCKER_VOL $DOCKER_ENV --net=host \
#SB 	$Test_Docker_Image -c \
#SB 	'source clientValidation.sh; cp client-validation.log artifacts/'
#SB    mv $WORKSPACE/artifacts/* $WORKSPACE/ || true
else
	echo "!!! I am not prepared to run for slc${singularity}."
    exit 1
fi

ERR=${ERR:-}
#1.1 Interim steps
#cd ${WORKSPACE}

cp $WORK_DIR/client-validation.log .

awk -v RS="____________" '/TEST_RESULT:\sFAILED/' RS="____________" client-validation.log > result_failed
awk -v RS="____________" '/TEST_RESULT:\sOK/' RS="____________" client-validation.log > result_OK


#2. Update issue with test results
TEST_RESULT='FAILED'
if [ -s "result_failed" ]; then
	echo -e "Some CRABClient commands failed. Find failed commands below:" >> message_CVResult_interim
	echo -e "\`\`\``cat result_failed`\n\`\`\`" >> message_CVResult_interim
	ERR=true
elif [ -s "result_OK" ]; then
	echo "All commands were executed successfully." >> message_CVResult_interim
    TEST_RESULT='SUCCEEDED'
else
	echo "Something went wrong. Investigate manually." >> message_CVResult_interim
    ERR=true
fi

BUILD_URL=https://gitlab.cern.ch

echo -e "**Test:** Client validation\n\
**Result:** ${TEST_RESULT}\n\
**Finished at:** `(date '+%Y-%m-%d %H:%M:%S')`\n\
**Test log:** ${BUILD_URL}console\n\
**All executed commands:** ${BUILD_URL}/artifact/client-validation.log/*view*/\n\
**Message:** `cat message_CVResult_interim`\n" > message_CVResult

#export PYTHONPATH=/cvmfs/cms-ib.cern.ch/jenkins-env/python/shared
#$WORKSPACE/cms-bot/create-gh-issue.py -r $Repo_GH_Issue -t "$issueTitle" -R message_CVResult

cat message_CVResult

if [[ -n $ERR ]] ; then
	exit 1
fi
