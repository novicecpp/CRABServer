FROM test2:latest as build-dir
FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705

USER root
#RUN apt install -y gfal2 gfal2-plugin-http gfal2-plugin-xrootd
RUN apt-get update \
    && apt-get install -y libsasl2-dev python3-dev libldap-dev libssl-dev \
    && apt-get clean all

ENV WDIR=/data
ENV USER=crab3
ENV WMCORE_TAG=2.2.4rc2
ENV CRABSERVER_TAG=v3.230921

RUN curl -ksLO https://raw.githubusercontent.com/dmwm/WMCore/$WMCORE_TAG/requirements.txt \
    && cat requirements.txt | grep -v gfal2 > req.txt \
    && pip install -r req.txt \
    && pip install --no-deps wmcore==$WMCORE_TAG \
    && pip install python-ldap==3.4.3

# add new user and switch to user
RUN useradd ${USER} \
    && install -o ${USER} -d ${WDIR} \
    && mkdir -p /opt/rucio/etc/

USER ${USER}


## add needed script (in a different line to avoid full rpm install when they change)
#COPY --chown=${USER}:${USER} addGH.sh ./
## add GitHub repositories
#RUN ./addGH.sh
#
## run the service
#CMD sh /data/run.sh && sh /data/monitor.sh && while true; do sleep 60;done

RUN mkdir -p /data/srv/tmp \
    && mkdir -p /data/srv/Publisher \
    && mkdir -p /data/srv/TaskManager

RUN cd /data/srv/TaskManager \
    && ln -sf /data/hostdisk/TaskWorker/cfg cfg \
    && ln -sf /data/hostdisk/TaskWorker/logs logs

COPY --from=build-dir /build/install_dir /data/srv/TaskManager/current

WORKDIR /data/srv/TaskManager

COPY rucio.cfg /opt/rucio/etc/
COPY --chown=1000:1000 start.sh /data/srv/TaskManager/

# this does not suppose to put these in prod
USER root
# crabconfig
#COPY TaskWorkerConfig.py /data/srv/TaskManager/
#RUN mkdir /data/certs
#cert
#COPY proxy_crab-dev-tw03.pem /data/certs/servicecert.pem
#COPY proxy_crab-dev-tw03.pem /data/certs/servicekey.pem
#RUN chown -R crab3:crab3 /data/certs/
#rucio
#grid security
#COPY grid-security /etc/grid-security





#    && unzip CRABServer.zip
