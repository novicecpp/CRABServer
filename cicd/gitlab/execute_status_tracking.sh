#! /bin/bash

cd "$(git rev-parse --show-toplevel)"
source test/container/testingScripts/setupCRABClient.sh;
test/container/testingScripts/statusTracking.py
