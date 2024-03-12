#!/bin/bash

set -euo pipefail
set -x

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

ls -l /cvmfs/cms-ib.cern.ch/latest/ 2>&1

#voms-proxy-init -rfc -voms cms -valid 192:00
#export X509_USER_CERT=/home/cmsbld/.globus/usercert.pem
#export X509_USER_KEY=/home/cmsbld/.globus/userkey.pem
#export PROXY=$(voms-proxy-info -path 2>&1)

# need these steps to make client read proxyfile properly
cp $X509_USER_PROXY proxyfile
chmod 0600 proxyfile
chown $(id -u):$(id -g) proxyfile
export X509_USER_PROXY="$(realpath proxyfile)"
export PROXY=${X509_USER_PROXY}
export X509_USER_CERT=$X509_USER_PROXY
export X509_USER_KEY=$X509_USER_PROXY

#git clone https://github.com/cms-sw/cms-bot

export ERR=false
#be aware that when running in singularity, we use ${WORK_DIR} set below,
#while if we run in CRAB Docker container, then ${WORK_DIR} set in Dockerfile.
#export WORK_DIR=`pwd`
#cp submitted_tasks $WORKSPACE/artifacts

export WORK_DIR=workdir
mkdir -p $WORK_DIR


#1. Start tests
if [ "X${singularity}" == X6 ] || [ "X${singularity}" == X7 ] || [ "X${singularity}" == X8 ]; then
	echo "Starting singularity ${singularity} container."
    #git clone https://github.com/$Repo_Testing_Scripts
    #cd CRABServer/test/container/testingScripts
    #git checkout $Branch_Testing_Scripts
    scramprefix=cc${singularity}
    if [ "X${singularity}" == X6 ]; then scramprefix=cc${singularity}; fi
    if [ "X${singularity}" == X7 ]; then scramprefix=el${singularity}; fi
    if [ "X${singularity}" == X8 ]; then scramprefix=el${singularity}; fi
	/cvmfs/cms.cern.ch/common/cmssw-${scramprefix} --  ${SCRIPT_DIR}/clientConfigurationValidation.sh || export ERR=true
else
	echo "!!! I am not prepared to run for slc${singularity}."
    exit 1
fi

#cd ${WORK_DIR}
#mv $WORKSPACE/artifacts/* $WORKSPACE/

#export RETRY=${NAGINATOR_COUNT:-0}
#export MAX_RETRY=${NAGINATOR_MAXCOUNT:-4}

#2. Update issue with test results

# make it not error from report below
MAX_RETRY=1
RETRY=1


TEST_RESULT='FAILED'
MESSAGE='Test failed. Investigate manually'
if [ -s "successful_tests" ] && [ ! -s "failed_tests" ]; then
	TEST_RESULT='SUCCEEDED'
    MESSAGE='Test is done.'
fi

declare -A results=( ["SUCCESSFUL"]=successful_tests ["FAILED"]=failed_tests ["RETRY"]=retry_tests)
for result in "${!results[@]}";
do
	if [ -s "${results[$result]}" ]; then
		test_result=`cat ${results[$result]}`
		echo -e "\n${result} TESTS:\n${test_result}" >> message_CCVResult_interim
        TEST_RESULT='FULL-STATUS-UNKNOWN'
	else
        TEST_RESULT='FULL-STATUS-UNKNOWN'
		echo -e "\n${result} TESTS:\n none" >> message_CCVResult_interim
	fi
done


echo -e "**Test:** Client configuration validation\n\
**Result:** ${TEST_RESULT}\n\
**Attempt:** ${RETRY} out of ${MAX_RETRY}. ${MESSAGE}\n\
**Finished at:** `(date '+%Y-%m-%d %H:%M:%S')`\n\
**Test log:** ${BUILD_URL}console\n" > message_CCVResult

echo -e "\`\`\``cat message_CCVResult_interim`\n\`\`\`"  >> message_CCVResult

#export PYTHONPATH=/cvmfs/cms-ib.cern.ch/jenkins-env/python/shared
#$WORKSPACE/cms-bot/create-gh-issue.py -r $Repo_GH_Issue -t "$issueTitle" -R message_CCVResult

if $ERR ; then
	exit 1
fi
if [[ $TEST_RESULT == 'FULL-STATUS-UNKNOWN' ]]; then
    exit 4
fi
