#! /bin/bash
# Command to build image in local machine
# $(git rev-parse --show-toplevel) always be the context dir of docker build, same as we run in CI.
docker build -t registry.cern.ch/cmscrab/crabserver:wmcore-pypi-devthree -f Dockerfile ../../
