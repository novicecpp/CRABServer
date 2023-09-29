FROM python:3.8 as wmcore-src
SHELL ["/bin/bash", "-c"]
COPY cicd/crabserver_pypi/ .
RUN req=($(./requirementsParse.py)) \
    && git clone ${req[0]} -b ${req[1]} /WMCore \
    && ( cd /WMCore; git status )

FROM python:3.8 as build-data
SHELL ["/bin/bash", "-c"]
RUN mkdir /build \
    && apt-get update \
    && apt-get install -y curl zip git \
    && apt-get clean all
WORKDIR /build
COPY cicd/crabtaskworker_pypi/new_htcondor_make_runtime.sh /build
COPY . /build
COPY --from=wmcore-src /WMCore /build/WMCore

RUN bash new_htcondor_make_runtime.sh
RUN mkdir /build/install_dir \
    && python3 setup.py install_system -s TaskWorker --prefix=/build/install_dir \
    && cp /build/CMSRunAnalysis.tar.gz /build/install_dir/data/ \
    && cp /build/TaskManagerRun.tar.gz /build/install_dir/data/

FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705
SHELL ["/bin/bash", "-c"]
RUN mkdir /build
WORKDIR /build
COPY . /build
#RUN apt install -y gfal2 gfal2-plugin-http gfal2-plugin-xrootd
RUN apt-get update \
    && apt-get install -y libsasl2-dev python3-dev libldap-dev libssl-dev \
    && apt-get clean all

ENV WDIR=/data
ENV USER=crab3

COPY --from=wmcore-src /WMCore/requirements.txt requirements.txt
RUN req=($(./cicd/crabserver_pypi/requirementsParse.py -f ./cicd/crabserver_pypi/wmcore_requirements.txt)) \
    && WMCORE_TAG=${req[1]} \
    && cat requirements.txt | grep -v gfal2 > req.txt \
    && pip install -r req.txt \
    && pip install --no-deps wmcore==${WMCORE_TAG} \
    && pip install python-ldap==3.4.3

# add new user and switch to user
RUN useradd ${USER} \
    && install -o ${USER} -d ${WDIR} \
    && mkdir -p /opt/rucio/etc/

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

COPY --from=build-data /build/install_dir /data/srv/TaskManager/current

WORKDIR /data/srv/TaskManager

COPY cicd/crabtaskworker_pypi/rucio.cfg /opt/rucio/etc/
COPY cicd/crabtaskworker_pypi/start.sh /data/srv/TaskManager/

RUN chown -R 1000:1000 /data

RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-crabserver

WORKDIR ${WDIR}
USER ${USER}

CMD while true; do sleep 3600;done
