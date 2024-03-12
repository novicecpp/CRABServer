#! /bin/bash
# ci global variable
export X509_USER_PROXY=/tmp/x509up_u1000

export CMSSW_release=CMSSW_13_0_2
#fixed vars
export CRABClient_version=prod
export CRABServer_tag=HEAD
export REST_Instance=test12
export Client_Configuration_Validation=true
#it should not need in future
export Repo_GH_Issue=novicecpp/CRABServer
export Repo_Testing_Scripts=novicecpp/CRABServer
export Branch_Testing_Scripts=wmcore_pypi
export Test_Docker_Image=registry.cern.ch/cmscrab/crabtesting:231009
#bash -x cicd/gitlab/execute_test.sh
