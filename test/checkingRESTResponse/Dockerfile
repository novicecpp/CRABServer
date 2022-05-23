FROM python:3.8-slim
ENV WMCORE_GIT=https://github.com/novicecpp/WMCore
ENV WMCORE_COMMIT=fff002bc2a547b8c9caabd58e49aed0ffebd5240
ENV CRABSERVER_GIT=https://github.com/dmwm/CRABServer
ENV CRABSERVER_COMMIT=acfdfbf5ade582c0b0462c224ed0f6b167539701
RUN apt-get update && apt-get install -y curl git gcc libssl-dev libcurl4-openssl-dev && apt-get clean
RUN pip install 'pycurl==7.43.0.6' 'future==0.18.2'
RUN mkdir -p /testsuite /data/repos \
    && cd /data/repos \
    && git clone $WMCORE_GIT \
    && cd WMCore \
    && git checkout $WMCORE_COMMIT \
    && cd .. \
    && git clone $CRABSERVER_GIT \
    && cd CRABServer \
    && git checkout $CRABSERVER_COMMIT \
    && cd ..
RUN curl -LO https://s3.cern.ch/swift/v1/crab_public/2022-05-23_grid-security-certificates_lxplus8.tar.gz \
    && curl -LO https://s3.cern.ch/swift/v1/crab_public/2022-05-23_grid-security-certificates_lxplus8.tar.gz.sha256 \
    && sha256sum -c 2022-05-23_grid-security-certificates_lxplus8.tar.gz.sha256 \
    && tar zxvf 2022-05-23_grid-security-certificates_lxplus8.tar.gz -C /etc
COPY . /testsuite
WORKDIR /testsuite
