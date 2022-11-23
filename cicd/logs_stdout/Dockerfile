ARG BASEIMAGE=registry.cern.ch/cmsweb/crabserver:v3.221027
FROM $BASEIMAGE
USER 0/config/crabserver/
RUN mkdir /tmp/hotpatch
COPY manage.diff run.sh.diff Main.py.diff /tmp/hotpatch/
RUN cd /tmp/hotpatch \
    && patch /data/srv/current/config/crabserver/manage < manage.diff \
    && patch /data/run.sh < run.sh.diff \
    && patch /data/srv/HG2211c-4af4331c5bb243725a2e84dd99dce990/sw.crab_master/slc7_amd64_gcc630/cms/crabserver/v3.221027-5b63787d5b5cb159ed9b77ebd5b7c760/lib/python3.8/site-packages/WMCore/REST/Main.py < Main.py.diff
USER 1000
