#! /bin/bash

set -eo pipefail

export BUILD_CAUSE_JSON=$(curl --silent ${BUILD_URL}/api/json | tr "{}" "\n" | grep "Started by")
export BUILD_USER_ID=$(echo $BUILD_CAUSE_JSON | tr "," "\n" | grep "userId" | awk -F\" '{print $4}')
export BUILD_USER_NAME=$(echo $BUILD_CAUSE_JSON | tr "," "\n" | grep "userName" | awk -F\" '{print $4}')
