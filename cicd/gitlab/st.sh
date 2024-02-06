#! /bin/bash

export SLEEP_SECONDS=900
export RETRY=5
export REST_Instance=test12
export CMSSW_release=CMSSW_13_0_2
export Check_Publication_Status=Yes
export CRABClient_version=prod
cp artifacts/submitted_tasks_TS artifacts/submitted_tasks
cat artifacts/submitted_tasks
RETRY_COUNT=1
while true; do
    echo "$RETRY_COUNT/$RETRY attempt."
    bash -x cicd/gitlab/check_test_result.sh || rc=$?
    if [[ $rc -ne 0 ]]; then
        echo "check_test_result.sh is fail with exit code $rc"
        echo "sleep for $SLEEP_SECONDS seconds"
        sleep $SLEEP_SECONDS
        if [[ $RETRY_COUNT -eq $RETRY ]]; then
            echo "Reach max retry count: $RETRY"
            exit 1
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        continue
    else
        break
    fi
done
