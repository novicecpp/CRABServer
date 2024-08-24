#! /bin/bash
ENV=test12
TAG=pypi-${ENV}-$(date +"%s")
git tag $TAG
git push gitlab $TAG -o ci.variable="BUILD=t"
