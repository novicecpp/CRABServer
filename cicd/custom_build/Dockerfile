FROM registry.cern.ch/cmsweb/crabserver:v3.220705
USER 0
RUN mkdir /tmp/build
COPY install.sh /tmp/build/install.sh
COPY CRABServer /tmp/build/CRABServer
COPY WMCore /tmp/build/WMCore
RUN ls -alh . \
    && cd /tmp/build/ \
    && bash install.sh \
    && rm -rf /tmp/build
USER 1000
