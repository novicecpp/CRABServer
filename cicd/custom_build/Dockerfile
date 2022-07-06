FROM registry.cern.ch/cmsweb/crabserver:v3.220705
USER 0
COPY . /tmp/context
RUN cd /tmp/context \
    && ls \
    && bash install.sh  \
    && cd -
    && rm -rf /tmp/context
USER 1000
