#! /bin/bash
# Container main process.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}"

# run monitoring script
if [ -f ./monitor.sh ]; then
    ./monitor.sh &
fi

# create named pipe to pipe log to stdout
mkfifo /data/srv/state/crabserver/crabserver-fifo
# Run cat on named pipe to prevent crabserver deadlock because no reader attach
# to pipe. It is safe because only single process can read from pipe at the time
cat /data/srv/state/crabserver/crabserver-fifo &

#start the service
#export CRYPTOGRAPHY_ALLOW_OPENSSL_102=true
./start.sh -c

# cat fifo forever to read logs
while true;
do
    cat /data/srv/state/crabserver/crabserver-fifo
done
