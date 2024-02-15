#! /bin/bash
# This script mean to run inside crabtaskworker image.

set -euo pipefail
set -x

INSTALL_DIR=/data/build/install_dir
RUNTIME_DIR=/data/build/make_runtime
WMCOREDIR=/data/repos/WMCore
CRABSERVERDIR=/data/repos/CRABServer
mkdir -p "${INSTALL_DIR}" "${RUNTIME_DIR}"
export INSTALL_DIR RUNTIME_DIR WMCOREDIR CRABSERVERDIR
pushd "${CRABSERVERDIR}"
bash cicd/crabtaskworker_pypi/build_data_files.sh
popd

DATA_DIR="$(dirname "$(find /data/srv/current -name TaskManagerRun.tar.gz)")"
BACKUP_DIR="$(realpath "${DATA_DIR/../../}")"
ORIGINAL_DATA_FILES_PATH=$BACKUP_DIR/Original_data_files.tar.gz
if [[ ! -f "${ORIGINAL_DATA_FILES_PATH}" ]]; then
    echo "Backup ./data directory to $ORIGINAL_DATA_FILES_PATH"
    tar -zcf "${ORIGINAL_DATA_FILES_PATH}" -C "${DATA_DIR/../}" data
fi
rm -rf "${DATA_DIR:?}/*"
cp "${INSTALL_DIR}/data/*" "${DATA_DIR}"
