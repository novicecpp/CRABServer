#! /bin/bash

# Parse deployment env from tag.
# - If match regexp `^pypi-(<env1>|<env2>|...)-.*`, set ENV_NAME to the string
#     in group.
# - If match release tag (e.g., v3.240501), set ENV_NAME to preprod
# Allow override ENV_NAME (from push option or WebUI)
# dot-env files are in ./env directory.

set -euo pipefail
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

TAG=$1
VALIDATE_DEV_TAG='^pypi-(devthree|preprod)-.*'
VALIDATE_RELEASE_TAG='^v3\.[0-9]{6}.*'
# Do not quote regexp vars here
if [[ $TAG =~ $VALIDATE_DEV_TAG ]]; then
    IFS='-' read -ra TMPSTR <<< "${TAG}"
    ENV_NAME=${ENV_NAME:-${TMPSTR[1]}}
elif [[ $TAG =~ $VALIDATE_RELEASE_TAG ]]; then
    ENV_NAME=${ENV_NAME:-preprod}
else
    >&2 echo "fail to parse env from string: $TAG"
    exit 1
fi

echo "Use env: ${ENV_NAME}"
cp "${SCRIPT_DIR}/env/${ENV_NAME}" .env
