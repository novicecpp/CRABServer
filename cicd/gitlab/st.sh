#! /bin/bash

#[ -f .counter ] || echo 0 > .counter
#export RETRY=$(cat .counter)
#Do whatever you need knowing it is retried
export REST_Instance=test12
export CMSSW_release=CMSSW_13_0_2
export Check_Publication_Status=Yes
export CRABClient_version=prod
cp artifacts/submitted_tasks_TS artifacts/submitted_tasks
sleep 900 #|| true  # cooldown for 15 mins, ignore if it get killed
bash -x cicd/gitlab/check_test_result.sh #|| rc=$?
#Increment value and update it to file
#if [[ $rc -ne 0 ]]; then
#    RETRY=$((RETRY+1))
#    echo $RETRY
#    echo $RETRY > .counter
#    exit 1
#else
#    exit 0
#fi
