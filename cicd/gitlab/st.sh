#! /bin/bash

export SLEEP_SECONDS=900
export RETRY=5
export REST_Instance=test12
export CMSSW_release=CMSSW_13_0_2
export Check_Publication_Status=Yes
export CRABClient_version=prod
cp artifacts/submitted_tasks_TS artifacts/submitted_tasks
for i in {1..$RETRY}; do
    echo "$i attempt."
    bash -x cicd/gitlab/check_test_result.sh || rc=$?
    if [[ $rc -ne 0 ]]; then
        echo "check_test_result.sh is fail with exit code $rc"
        echo "sleep for $SLEEP_SECONDS seconds"
        sleep $SLEEP_SECONDS
        continue
    else
        exit 0
    fi
done
