#! /bin/bash
# Simplify version of htcondor_make_runtime.sh
# https://github.com/novicecpp/CRABServer/blob/5dd0a31c9545e5e16a395aba0b1b955f1bf37b23/bin/htcondor_make_runtime.sh
# This script needs:
#   - a cloned WMCore repo at the top of CRABServer respository.
#   - fresh CRABServer and WMCore clone.
#   -
# See cicd/crabtaskworker_pypi/Dockerfile at wmcore-src and build-data layer.
# To avoid mess with local directory, run this script inside docker.

set -euo pipefail
set -x

# env var can override.
RUNTIME_DIR="${RUNTIME_DIR:-./make_runtime}"
WMCOREDIR="${WMCOREDIR:-../WMCore}"
CRABSERVERDIR="${CRABSERVERDIR:-.}"

# get absolute path
RUNTIME_DIR="$(realpath "${RUNTIME_DIR}")"
WMCOREDIR="$(realpath "${WMCOREDIR}")"
CRABSERVERDIR="$(realpath "${CRABSERVERDIR}")"

BUILDDIR="${RUNTIME_DIR}"
STARTDIR="${BUILDDIR}/runtime"
WMCORE_BUILD_PREFIX="${WMCOREDIR}/build/lib"
CRABSERVER_BUILD_PREFIX="${CRABSERVERDIR}/build/lib"

# cleanup $BUILDDIR
rm -rf "${BUILDDIR}"
# create neccessary dir
mkdir -p "${BUILDDIR}" "${STARTDIR}" "${CRABSERVER_BUILD_PREFIX}" "${WMCORE_BUILD_PREFIX}"

pushd "${WMCOREDIR}" || exit
python3 setup.py build_system -s crabtaskworker --skip-docs
popd

pushd "${CRABSERVERDIR}" || exit
python3 setup.py build_system -s TaskWorker --skip-docs=d
popd


pushd $STARTDIR

# make sure there's always a CRAB3.zip to avoid errors in other parts
pwd
echo $STARTDIR
touch $STARTDIR/dummyFile
zip -r $STARTDIR/CRAB3.zip $STARTDIR/dummyFile
rm -f $STARTDIR/dummyFile

# Take the libraries from the build environment.
RELEASE=1
if [[ "x$RELEASE" != "x" ]]; then
    # I am inside  a release building
    pushd "${WMCORE_BUILD_PREFIX}"
    zip -r $STARTDIR/WMCore.zip *
    zip -rq $STARTDIR/CRAB3.zip WMCore PSetTweaks Utils -x \*.pyc || exit 3
    popd

    pushd "${CRABSERVER_BUILD_PREFIX}"
    zip -rq $STARTDIR/CRAB3.zip RESTInteractions.py HTCondorUtils.py HTCondorLocator.py TaskWorker CRABInterface  TransferInterface ASO -x \*.pyc || exit 3
    popd

    mkdir -p bin
    cp -r $CRABSERVERDIR/scripts/{TweakPSet.py,CMSRunAnalysis.py,task_process} .
    cp $CRABSERVERDIR/src/python/{ServerUtilities.py,RucioUtils.py,CMSGroupMapper.py,RESTInteractions.py} .
fi

pwd
echo "Making TaskManagerRun tarball"
tar zcf $BUILDDIR/TaskManagerRun.tar.gz CRAB3.zip TweakPSet.py CMSRunAnalysis.py task_process ServerUtilities.py RucioUtils.py CMSGroupMapper.py RESTInteractions.py || exit 4
echo "Making CMSRunAnalysis tarball"
tar zcf $BUILDDIR/CMSRunAnalysis.tar.gz WMCore.zip TweakPSet.py CMSRunAnalysis.py ServerUtilities.py CMSGroupMapper.py RESTInteractions.py || exit 4
# cleanup. $BUILDDIR (current directory) should only have TaskManagerRun.tar.gz and CMSRunAnalysis.tar.gz
rm -rf "${STARTDIR}" "${WMCORE_BUILD_PREFIX}" "${CRABSERVER_BUILD_PREFIX}"
popd
