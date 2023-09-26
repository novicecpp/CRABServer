FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705
ENV WDIR=/data
ENV USER=crab3
RUN mkdir /build
WORKDIR /build
COPY requirements.txt /build
RUN pip install -r /build/requirements.txt
RUN useradd ${USER} \
    && install -o ${USER} -d ${WDIR} \
    && mkdir -p /opt/rucio/etc/
#USER ${USER}
SHELL ["/bin/bash", "-c"]
RUN curl -Lo WMCore.tar.gz https://github.com/dmwm/WMCore/archive/refs/tags/2.2.4rc5.tar.gz \
    && curl -Lo CRABServer.tar.gz https://github.com/dmwm/CRABServer/archive/refs/tags/v3.230921.tar.gz
RUN mkdir -p \
    /data/srv/current/lib/python3.8/site-packages/ \
    /build/WMCore \
    /build/CRABServer \
    /data/srv/current/bin \
    && tar -zxf WMCore.tar.gz --strip-components=1 -C WMCore \
    && tar -zxf CRABServer.tar.gz --strip-components=1 -C CRABServer \
    && cp -r CRABServer/src/python/* /data/srv/current/lib/python3.8/site-packages/ \
    && cp -r WMCore/src/python/WMCore /data/srv/current/lib/python3.8/site-packages/ \
    && cp -r WMCore/src/python/Utils /data/srv/current/lib/python3.8/site-packages/ \
    && cp WMCore/bin/wmc-httpd /data/srv/current/bin
RUN ls /data/srv/current/ \
    && install -d -o ${USER} -g ${USER} /data/srv/logs/crabserver \
    && install -d -o ${USER} -g ${USER} /data/srv/state/crabserver \
    && install -d -o ${USER} -g ${USER} /data/srv/current/auth/crabserver \
    && install -d -o ${USER} -g ${USER} /data/srv/current/config/crabserver

RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-crabserver
RUN apt-get update && apt-get install -y tini && apt-get clean all

COPY run.sh manage entrypoint.sh /data/

WORKDIR ${WDIR}
USER ${USER}
CMD /data/run.sh

# test
