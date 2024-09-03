#!/bin/bash
set -euo pipefail

reqfile=${1}
wmcore_repo="$(grep -v '^\s*#' "${reqfile}" | cut -d' ' -f1)"
wmcore_version="$(grep -v '^\s*#' "${reqfile}" | cut -d' ' -f2)"
if [[ ${wmcore_repo} =~ /github.com\/dmwm\/WMCore ]]; then
    echo "Installing WMCore ${wmcore_version} from official repository via pip..."
    pip install --no-deps "wmcore==${wmcore_version}"
else
    # simply copy all src/python to install directory
    echo "Installing WMCore ${wmcore_version} from ${wmcore_repo} via clone..."
    git clone  --depth 1 "${wmcore_repo}" -b "${wmcore_version}" WMCore
    cp -rp WMCore/src/python/* /data/srv/current/lib/python/site-packages/
fi
