SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
git pull
source $SCRIPT_DIR/env_local.sh
bash "$@"
