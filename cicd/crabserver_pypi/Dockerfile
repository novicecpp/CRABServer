# Weird enough that we cannot use tnsnames from koji build
#FROM almalinux:8 as tnsnames
#
#RUN curl -Lo tnsnames.rpm https://koji.cern.ch/kojifiles/packages/oracle-instantclient-tnsnames.ora/1.4.6/1.rh8.cern/noarch/oracle-instantclient-tnsnames.ora-1.4.6-1.rh8.cern.noarch.rpm \
#    && rpm2archive tnsnames.rpm \
#    && tar -zxvf tnsnames.rpm.tgz  --strip-components=1 \
#    && ls -ahl
FROM registry.cern.ch/cmsweb/cmsweb:20230427-stable as tnsnames

FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705

ARG WMCORE_TAG
ARG CRABSERVER_TAG

ENV WDIR=/data
ENV USER=crab3
RUN apt-get update && apt-get install -y tini && apt-get clean all
RUN mkdir /build
WORKDIR /build
COPY requirements.txt /build
RUN pip install -r /build/requirements.txt
RUN useradd ${USER} \
    && install -o ${USER} -d ${WDIR} \
    && mkdir -p /opt/rucio/etc/
#USER ${USER}
SHELL ["/bin/bash", "-c"]
#RUN curl -Lo WMCore.tar.gz https://github.com/dmwm/WMCore/archive/refs/tags/${WMCORE_TAG}.tar.gz \
#    && curl -Lo CRABServer.tar.gz https://github.com/dmwm/CRABServer/archive/refs/tags/${CRABSERVER_TAG}.tar.gz
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
    && cp WMCore/bin/wmc-httpd /data/srv/current/bin \
    && rm -rf /build
RUN ls /data/srv/current/ \
    && install -d -o ${USER} -g ${USER} /data/srv/logs/crabserver \
    && install -d -o ${USER} -g ${USER} /data/srv/state/crabserver \
    && install -d -o ${USER} -g ${USER} /data/srv/current/auth/crabserver \
    && install -d -o ${USER} -g ${USER} /data/srv/current/config/crabserver

RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-crabserver

COPY run.sh manage entrypoint.sh env.sh /data/
COPY --from=tnsnames /etc/tnsnames.ora /etc/tnsnames.ora

WORKDIR ${WDIR}
USER ${USER}
CMD /data/run.sh

# test
