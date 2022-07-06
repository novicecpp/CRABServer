FROM registry.cern.ch/cmsweb/crabserver:v3.220705
USER 0
COPY . /tmp/context
RUN bash /tmp/context/install.sh && rm -rf /tmp/context
USER 1000
