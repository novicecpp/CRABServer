#! /bin/bash

# Parse deployment env from tag.
# - If match regexp `^pypi-(<env1>|<env2>|...)-.*`, set ENV_NAME to the string
#     in group. Valide env are preprod/test2/test11/test2
# - If match release tag (e.g., v3.240501), set ENV_NAME to preprod
#   - If tag have double underscore, the RELEASE_NAME (for final image tag) is
#       the left side.
#
# Allow override ENV_NAME (from push option or WebUI)
# dot-env files are in ./env directory.

set -euo pipefail
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

TAG=$1
VALIDATE_DEV_TAG='^pypi-(preprod|test2|test11|test12)-.*'
VALIDATE_RELEASE_TAG='^v3\.[0-9]{6}.*'
if [[ $TAG =~ $VALIDATE_DEV_TAG ]]; then # Do not quote regexp variable here
    IFS='-' read -ra TMPSTR <<< "${TAG}"
    ENV_NAME=${ENV_NAME:-${TMPSTR[1]}}
elif [[ $TAG =~ $VALIDATE_RELEASE_TAG ]]; then
    ENV_NAME=${ENV_NAME:-test12}
else
    >&2 echo "fail to parse env from string: $TAG"
    exit 1
fi

# Get the left side of tag
# e.g., v3.220220.test1__1716292861, the release name will be v3.220220.test1
VALIDATE_SPLITTER="^.+__.+"
if [[ $TAG =~ $VALIDATE_SPLITTER ]]; then
    IFS='__' read -ra TMPARRAY <<< "${TAG}"
    RELEASE_NAME="${TMPARRAY[0]}-stable"
else
    RELEASE_NAME="${TAG}-stable"
fi

echo "Use env: ${ENV_NAME}"
echo "Release tag: ${RELEASE_NAME}"
cp "${SCRIPT_DIR}/env/${ENV_NAME}" .env
echo "RELEASE_NAME=${RELEASE_NAME}" >> .env
echo ".env content:"
cat .env
