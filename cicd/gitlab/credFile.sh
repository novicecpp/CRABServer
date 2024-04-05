#! /bin/bash
set -euo pipefail

CREDS_FILE=$1
CREDS_COPIED=$(basename ${CREDS_COPIED})_copy
cp ${CREDS_FILE} ${CREDS_COPIED}
#echo >> ${CRAB_TW_SSH_KEY_COPIED}
chown $(id -u):$(id -g) "${CREDS_COPIED}"
chmod 0600 "${CREDS_COPIED}"
echo "${CREDS_COPIED}"
