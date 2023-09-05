FROM registry.cern.ch/cmsweb/crabserver:v3.220705
RUN mkdir /tmp/build
COPY --chown=1000:1000 crabtaskworker/install.sh /tmp/build/install.sh
COPY --chown=1000:1000 latest/CRABServer /tmp/build/CRABServer
COPY --chown=1000:1000 latest/WMCore /tmp/build/WMCore
RUN ls -alh . \
    && cd /tmp/build/ \
    && bash install.sh \
    && rm -rf /tmp/build
USER 1000
