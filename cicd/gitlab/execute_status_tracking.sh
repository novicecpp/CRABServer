#! /bin/bash
set -x
echo "(DEBUG) X509_USER_PROXY=${X509_USER_PROXY}"
echo "(DEBUG) ROOT_DIR=${ROOT_DIR}"
echo "(DEBUG) WORK_DIR=${WORK_DIR}"

source "${ROOT_DIR}"/cicd/gitlab/setupCRABClient.sh;
python3 "${ROOT_DIR}"/cicd/gitlab/statusTracking.py
