#! /bin/bash

export SLEEP_SECONDS=900
export RETRY=${RETRY:-5}

# use in check_test_result.sh and statusTracking.py
export CMSSW_release=CMSSW_13_0_2
export SCRAM_ARCH=el8_amd64_gcc11
export REST_Instance=test12
export Check_Publication_Status=Yes
export CRABClient_version=prod


export SUBMITTED_TASKS_PATH=artifacts/submitted_tasks_TS



echo "\"${SUBMITTED_TASKS_PATH}\" content: "
cat "${SUBMITTED_TASKS_PATH}" || rc="$?"
[[ -n "$rc" ]] && exit $rc
cp "${SUBMITTED_TASKS_PATH}" artifacts/submitted_tasks
RETRY_COUNT=1
while true; do
    echo "$RETRY_COUNT/$RETRY attempt."
    bash -x cicd/gitlab/check_test_result.sh || rc=$?
    if [[ -n $rc ]]; then
        echo "check_test_result.sh is fail with exit code $rc"
        if [[ $rc == 4 ]]; then
            if [[ $RETRY_COUNT -eq $RETRY ]]; then
                echo "Reach max retry count: $RETRY"
                exit 1
            fi
            echo "sleep for $SLEEP_SECONDS seconds"
            echo "retrying..."
            sleep $SLEEP_SECONDS
            RETRY_COUNT=$((RETRY_COUNT + 1))
            continue
        else
            echo "unexpected error"
            exit 1
        fi

    else
        break
    fi
done
