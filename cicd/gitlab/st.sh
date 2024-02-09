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

export WORKSPACE=testsuite
export ROOT_DIR=$PWD

# copy proxyfile and correct permission
# not sure why need, but fix like this is worked when run in runner
X509_USER_PROXY="${X509_USER_PROXY:-/tmp/x509up_u$(id -u)}"
echo "$X509_USER_PROXY"
ls -alh $X509_USER_PROXY
cp $X509_USER_PROXY $WORKSPACE/proxyfile
chmod 600 $WORKSPACE/proxyfile
chown $(id -u):$(id -g) $WORKSPACE/proxyfile
export X509_USER_PROXY=$(realpath $WORKSPACE/proxyfile)
cat $X509_USER_PROXY | head -n10

# temp create workspace and artifacts dir
# the artifacts dir should not hardcode in statusTracking.py script)
mkdir -p $WORKSPACE/artifacts
if [[ -z "${Manual_Task_Names}" ]]; then
    cp artifacts/submitted_tasks_TS artifacts/submitted_tasks || exit
else
    echo "${Manual_Task_Names}" > $WORKSPACE/artifacts/submitted_tasks
fi

# retry machanism
RETRY_COUNT=1
while true; do
    echo "$RETRY_COUNT/$RETRY attempt."
    pushd $WORKSPACE || exit
    bash -x ../cicd/gitlab/check_test_result.sh || rc=$?
    popd || exit
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
