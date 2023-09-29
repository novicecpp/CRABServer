#! /bin/bash

if [ -f /data/monitor.sh ]; then
    /data/monitor.sh &
fi

mkfifo /data/srv/state/crabserver/crabserver-fifo
# Run cat on named pipe to prevent crabserver deadlock because no reader attach
# to pipe. It is safe because only single process can read from pipe at the time
cat /data/srv/state/crabserver/crabserver-fifo &

#start the service
#export CRYPTOGRAPHY_ALLOW_OPENSSL_102=true
/data/manage start

# cat fifo forever to read logs
while true;
do
    cat /data/srv/state/crabserver/crabserver-fifo
done

#export X509_USER_CERT=/testdir/x509up_u1000
#export X509_USER_KEY=/testdir/x509up_u1000
# run monitoring script
