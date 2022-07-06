FROM registry.cern.ch/cmsweb/crabserver:v3.220705
USER 0
ARG CRABSERVER_REPO
ARG CRABSERVER_BRANCH
ARG WMCORE_REPO
ARG WMCORE_BRANCH
COPY install.sh /tmp/install.sh
RUN bash /tmp/install.sh && rm /tmp/install.sh
USER 1000
