#! /bin/bash
set -euo pipefail
# test
ROOT_DIR="$(git rev-parse --show-toplevel)"
pushd "${ROOT_DIR}"
# clean workdir
rm -rf "${ROOT_DIR}/workdir"
export X509_USER_PROXY=/tmp/x509up_u1000
# from .env
export KUBECONTEXT=cmsweb-test12
export TW_MACHINE=crab-dev-tw03
export REST_Instance=test12
# ci
export X509_USER_PROXY="$(cicd/gitlab/credFile.sh $X509_USER_PROXY)"
export CRABClient_version=prod
export CRABServer_tag=HEAD
export REST_Instance # from .env
export CMSSW_release=CMSSW_13_0_2
export Task_Submission_Status_Tracking=true
export Check_Publication_Status=true
bash -x cicd/gitlab/execute_test.sh
popd
