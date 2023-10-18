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

FROM registry.cern.ch/cmsweb/gfal:latest as wmcore-gfal
SHELL ["/bin/bash", "-c"]
RUN pushd /data/miniconda \
    && git clone https://gitlab.cern.ch/dmc/gfal2-util -b v1.8.0 \
    && pushd gfal2-util \
    && python setup.py install \
    && popd \
    && rm -rf gfal2-util

FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:20231001-1.x86_64 as cern-cc7

FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705
SHELL ["/bin/bash", "-c"]
ENV USER=crab3

# gfal
COPY --from=wmcore-gfal /data/miniconda /data/miniconda
RUN ln -sf /data/miniconda/bin/gfal-ls /usr/bin/gfal-ls \
    && ln -sf /data/miniconda/bin/gfal-rm /usr/bin/gfal-rm \
    && ln -sf /data/miniconda/bin/gfal-copy /usr/bin/gfal-copy \
    && ln -sf /data/miniconda/bin/gfal-sum /usr/bin/gfal-sum

RUN mkdir /build
WORKDIR /build

# install package from os repository
RUN apt-get update \
    && apt-get install -y tini libsasl2-dev python3-dev libldap-dev libssl-dev \
    && apt-get clean all

# add new user and switch to user
RUN useradd ${USER} \
    && install -o ${USER} -d /data \
    && mkdir -p /opt/rucio/etc/

COPY cicd/crabserver_pypi/requirementsParse.py cicd/crabserver_pypi/wmcore_requirements.txt /build

# install dependencies
COPY --from=wmcore-src /WMCore/requirements.txt requirements.txt
RUN find /build
RUN req=($(/build/requirementsParse.py -f /build/wmcore_requirements.txt)) \
    && WMCORE_TAG=${req[1]} \
    && cat requirements.txt | grep -v gfal2 > req.txt \
    && pip install -r req.txt \
    && pip install --no-deps wmcore==${WMCORE_TAG} \
    && pip install python-ldap==3.4.3
COPY --from=cern-cc7 /etc/openldap /etc/openldap

# install crabserver
# will replace with pip later
COPY src/python/ /data/srv/current/lib/python3.8/site-packages/
COPY --from=build-data /build/install_dir/data /data/srv/current/lib/python3.8/site-packages/data

# create working directory
RUN mkdir -p /data/srv/tmp \
    && mkdir -p /data/srv/Publisher \
    && mkdir -p /data/srv/TaskManager

RUN cd /data/srv/TaskManager \
    && ln -sf /data/hostdisk/TaskWorker/cfg cfg \
    && ln -sf /data/hostdisk/TaskWorker/logs logs

WORKDIR /data/srv/TaskManager

COPY cicd/crabtaskworker_pypi/rucio.cfg /opt/rucio/etc/
COPY cicd/crabtaskworker_pypi/start.sh  cicd/crabtaskworker_pypi/run.sh /data/srv/TaskManager/

RUN chown -R 1000:1000 /data

# for debuggin purpose, we should not allow sudo in container
RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-crab3

## add needed script (in a different line to avoid full rpm install when they change)
#COPY --chown=${USER}:${USER} addGH.sh ./
## add GitHub repositories
#RUN ./addGH.sh

# clean up
RUN rm -rf /build

WORKDIR /data
USER ${USER}

ENTRYPOINT ["tini", "--"]
CMD bash
