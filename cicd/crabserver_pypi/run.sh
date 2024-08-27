#! /bin/bash
# Container main process.

set -euo pipefail

# run monitoring script
if [ -f /data/monitor.sh ]; then
    /data/monitor.sh &
fi

# create named pipe to pipe log to stdout
mkfifo /data/srv/state/crabserver/crabserver-fifo
# Run cat on named pipe to prevent crabserver deadlock because no reader attach
# to pipe. It is safe because only single process can read from pipe at the time
cat /data/srv/state/crabserver/crabserver-fifo &

#start the service
./manage.py start -c -s REST

# trap sigterm to trigger stop process command
stop_proc() {
    echo "Receiving SIGTERM. Stopping wmc-httpd..."
    ./manage.py stop
}
trap stop_proc SIGTERM

# cat fifo forever to read logs
while true;
do
    # make it background and wait
    # Ref: https://github.com/moby/moby/issues/33319#issuecomment-457914349
    # and https://github.com/dmwm/CMSKubernetes/blob/ca9926d20680fad639f2135d57fbe3376750e7b7/docker/pypi/wmagent/run.sh#L44-L45
    cat /data/srv/state/crabserver/crabserver-fifo &
    wait
done
