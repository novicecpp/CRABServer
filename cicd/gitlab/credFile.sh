#! /bin/bash
set -euo pipefail

CREDS_FILE=$1
CREDS_TYPE=$2

case "${CREDS_TYPE}" in
    x509)
        rc=0
        >&2 openssl x509 -checkend 0 -noout -in "${CREDS_FILE}" || rc=$?
        if [[ "${rc}" -ne 0 ]]; then
            >&2 echo "Proxy file has expired. Generating new one from local cert..."
            voms-proxy-init --rfc --voms cms -valid 196:00
            CREDS_FILE="$(voms-proxy-info -path)"
        fi
        ;;
    ssh)
        : # noop
        ;;
    *)
      >&2 echo "ERROR: Unknown CREDS_TYPE: ${CREDS_TYPE}"
      exit 1
      ;;
esac

CREDS_COPIED=$(basename ${CREDS_FILE})_copy
cp ${CREDS_FILE} ${CREDS_COPIED}
chown $(id -u):$(id -g) "${CREDS_COPIED}"
chmod 0600 "${CREDS_COPIED}"
realpath "${CREDS_COPIED}"
