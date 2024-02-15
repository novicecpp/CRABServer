#! /bin/bash

set -euo pipefail
set -x

RUNTIME_DIR="${RUNTIME_DIR:-./make_runtime}"
INSTALL_DIR="${INSTALL_DIR:-./install_dir}"

# get absolute path
RUNTIME_DIR="$(realpath "${RUNTIME_DIR}")"
INSTALL_DIR="$(realpath "${INSTALL_DIR}")"

# cleanup $INSTALL_DIR
rm -rf "${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"

# re export
bash cicd/crabtaskworker_pypi/new_htcondor_make_runtime.sh

python3 setup.py install_system -s TaskWorker --prefix="${INSTALL_DIR}"
cp "${RUNTIME_DIR}/CMSRunAnalysis.tar.gz" "${RUNTIME_DIR}/TaskManagerRun.tar.gz" \
   "${INSTALL_DIR}/data"
rm -rf "${INSTALL_DIR:?}/lib" # fix SC2115
