#! /bin/bash

# This script prepare the host environment for running one CRAB service based
# on CRAB TaskWorker container image and runs it. This file is specific for
# Publisher.
#
# This script must place in the same directory as `start.sh` script (usually
# `/data/srv/Publisher`) and meant to be called as CMD, by specify `-c /data/srv/Publisher/run.sh`
#  to `runContainer.sh` script.
# Please see https://github.com/dmwm/CRABServer/blob/master/src/script/Container/runContainer.sh
# and https://github.com/dmwm/CRABServer/blob/master/cicd/gitlab/deployTW.sh for example.
#
# This script require the following environment variables:
#   SERVICE   : the name of the service to be run: Publisher_schedd, Publisher_rucio etc.

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}"

# ensure container has needed mounts
check_link() {
    # function checks if symbolic links required to start service exists and if they are not broken
    if [[ -L "${1}" ]] ; then
        if [[ -e "${1}" ]] ; then
            return 0
        else
            unlink "${1}"
            return 1
        fi
    else
        return 1
    fi
}

# directories/files that should be created before starting the container
declare -A links=(
    ["logs"]="/data/hostdisk/${SERVICE}/logs"
    ["cfg"]="/data/hostdisk/${SERVICE}/cfg"
    ["/data/srv/Publisher_files"]="/data/hostdisk/${SERVICE}/PublisherFiles"
)

for name in "${!links[@]}";
do
  check_link "${name}" || ln -s "${links[$name]}" "$name"
done

# execute
./start.sh -c

while true; do
    sleep 3600
done
