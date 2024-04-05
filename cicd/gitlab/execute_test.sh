#! /bin/bash
set -euo pipefail

#00. check parameters
# note: make sure $X509_USER_PROXY is single file with correct permission, ready to consume without issuing with voms-proxy-init again
echo "(DEBUG) X509_USER_PROXY: ${X509_USER_PROXY}"
echo "(DEBUG) CRABClient_version: ${CRABClient_version}"
echo "(DEBUG) REST_Instance: ${REST_Instance}"
echo "(DEBUG) CMSSW_release: ${CMSSW_release}"
echo "(DEBUG) Client_Validation_Suite: ${Client_Validation_Suite}"
echo "(DEBUG) Client_Configuration_Validation: ${Client_Configuration_Validation:-}"
echo "(DEBUG) Task_Submission_Status_Tracking: ${Task_Submission_Status_Tracking:-}"
echo "(DEBUG) Check_Publication_Status: ${Check_Publication_Status:-false}"

# always run inside ./workdir
export ROOT_DIR=$PWD
export WORK_DIR=$PWD/workdir
mkdir -p workdir
pushd "${WORK_DIR}"




# Get configuration from CMSSW_release
CONFIG_LINE="$(grep "CMSSW_release=${CMSSW_release};" test/testingConfigs)"
SCRAM_ARCH="$(echo "${CONFIG_LINE}" | tr ';' '\n' | grep SCRAM_ARCH | sed 's|SCRAM_ARCH=||')"
inputDataset="$(echo "${CONFIG_LINE}" | tr ';' '\n' | grep inputDataset | sed 's|inputDataset=||')"
# see https://github.com/dmwm/WMCore/issues/11051 for info about SCRAM_ARCH formatting
singularity="$(echo "${SCRAM_ARCH}" | cut -d"_" -f 1 | tail -c 2)"
export SCRAM_ARCH inputDataset singularity

if [ "X${singularity}" == X6 ] || [ "X${singularity}" == X7 ] || [ "X${singularity}" == X8 ]; then
    echo "Starting singularity ${singularity} container."
    if [ "X${singularity}" == X6 ]; then scramprefix=cc${singularity}; fi
    if [ "X${singularity}" == X7 ]; then scramprefix=el${singularity}; fi
    if [ "X${singularity}" == X8 ]; then scramprefix=el${singularity}; fi
    ERR=false
    /cvmfs/cms.cern.ch/common/cmssw-${scramprefix} -- "${ROOT_DIR}"/cicd/gitlab/taskSubmission.sh || ERR=true
else
    echo "!!! I am not prepared to run for slc${singularity}."
    exit 1
fi

#cd ${WORK_DIR}
#mv $WORKSPACE/artifacts/* $WORKSPACE/

#4. Update issue with submission results
if $ERR ; then
    echo -e "Something went wrong during task submission. Find submission log [here](${BUILD_URL}console). None of the downstream jobs were triggered." >> message_taskSubmitted
else
    declare -A tests=( ["Task_Submission_Status_Tracking"]=submitted_tasks_TS ["Client_Validation_Suite"]=submitted_tasks_CV ["Client_Configuration_Validation"]=submitted_tasks_CCV)
    for test in "${!tests[@]}";
    do
        path="${WORK_DIR}/${tests[$test]}"
        if [ -s "$path"  ]; then
            echo -e "Task submission for **${test}** successfully ended.\n\`\`\`\n`cat "$path"`\n\`\`\`\n" >> message_taskSubmitted
        fi
    done
    echo -e "Finished at: `(date '+%Y-%m-%d %H:%M:%S')`\nFind submission log [here](${BUILD_URL}console)" >> message_taskSubmitted
fi

#sleep 20
#$WORKSPACE/cms-bot/create-gh-issue.py -r $Repo_GH_Issue -t "$issueTitle" -R message_taskSubmitted

#cp parameters $WORKSPACE/artifacts

if $ERR ; then
    exit 1
fi
