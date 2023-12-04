<<<<<<< HEAD
# caching wmcore src, need for building TaskManagerRun.tar.gz
FROM python:3.8 as wmcore-src
SHELL ["/bin/bash", "-c"]
# Use the "magic" requirements.txt from crabserver pypi
COPY cicd/crabserver_pypi/ .
RUN req=($(./requirementsParse.py)) \
    && git clone ${req[0]} -b ${req[1]} /WMCore \
    && ( cd /WMCore; git status ) \
    && echo "${req[1]}" > /wmcore_version

# create TaskManagerRun.tar.gz
=======
FROM python:3.8 as wmcore-src
SHELL ["/bin/bash", "-c"]
COPY cicd/crabserver_pypi/ .
RUN req=($(./requirementsParse.py)) \
    && git clone ${req[0]} -b ${req[1]} /WMCore \
    && ( cd /WMCore; git status )

>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))
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

<<<<<<< HEAD
# gfal, wmcore only has gfal lib but not cli
=======
>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))
FROM registry.cern.ch/cmsweb/gfal:latest as wmcore-gfal
SHELL ["/bin/bash", "-c"]
RUN pushd /data/miniconda \
    && git clone https://gitlab.cern.ch/dmc/gfal2-util -b v1.8.0 \
    && pushd gfal2-util \
    && python setup.py install \
    && popd \
    && rm -rf gfal2-util

<<<<<<< HEAD
# cern ldap config
FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:20231001-1.x86_64 as cern-cc7

# start image
FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705
SHELL ["/bin/bash", "-c"]
ENV USER=crab3
ENV WDIR=/data

# prepare build
RUN mkdir /build
WORKDIR /build

# install gfal
# symlink to workaround calling gfal from absolute path
=======
FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:20231001-1.x86_64 as cern-cc7

FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705
SHELL ["/bin/bash", "-c"]
ENV USER=crab3

# gfal
>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))
COPY --from=wmcore-gfal /data/miniconda /data/miniconda
RUN ln -sf /data/miniconda/bin/gfal-ls /usr/bin/gfal-ls \
    && ln -sf /data/miniconda/bin/gfal-rm /usr/bin/gfal-rm \
    && ln -sf /data/miniconda/bin/gfal-copy /usr/bin/gfal-copy \
    && ln -sf /data/miniconda/bin/gfal-sum /usr/bin/gfal-sum

<<<<<<< HEAD
# install package from debian repository
# deps for openldap: libsasl2-dev python3-dev libldap-dev libssl-dev
=======
RUN mkdir /build
WORKDIR /build

# install package from os repository
>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))
RUN apt-get update \
    && apt-get install -y tini libsasl2-dev python3-dev libldap-dev libssl-dev \
    && apt-get clean all

<<<<<<< HEAD
=======
# add new user and switch to user
RUN useradd ${USER} \
    && install -o ${USER} -d /data \
    && mkdir -p /opt/rucio/etc/
>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))

COPY cicd/crabserver_pypi/requirementsParse.py cicd/crabserver_pypi/wmcore_requirements.txt /build

# install dependencies
COPY --from=wmcore-src /WMCore/requirements.txt requirements.txt
<<<<<<< HEAD
COPY --from=wmcore-src /wmcore_version wmcore_version
RUN WMCORE_TAG=$(cat wmcore_version) \
    && cat requirements.txt | grep -v gfal2 > req.txt \
    && pip install -r req.txt \
    && pip install python-ldap==3.4.3 \
    && pip install --no-deps wmcore==${WMCORE_TAG}

# copy cern openldap config
COPY --from=cern-cc7 /etc/openldap /etc/openldap

# copy rucio config
RUN mkdir -p /opt/rucio/etc/
COPY cicd/crabtaskworker_pypi/rucio.cfg /opt/rucio/etc/

# install crabserver
# will replace with pip later
COPY src/python/ ${WDIR}/srv/current/lib/python3.8/site-packages/
# copy TaskManagerRun.tar.gz
COPY --from=build-data /build/install_dir/data ${WDIR}/srv/current/lib/python3.8/site-packages/data

# clean up
WORKDIR /data
RUN rm -rf /build

# add new user and switch to user
RUN useradd ${USER} \
    && install -o ${USER} -d ${WDIR}

# create working directory
RUN mkdir -p ${WDIR}/srv/tmp \
    && mkdir -p ${WDIR}/srv/Publisher \
    && mkdir -p ${WDIR}/srv/TaskManager

RUN cd ${WDIR}/srv/TaskManager \
    && ln -sf ${WDIR}/hostdisk/TaskWorker/cfg cfg \
    && ln -sf ${WDIR}/hostdisk/TaskWorker/logs logs
COPY cicd/crabtaskworker_pypi/start.sh  cicd/crabtaskworker_pypi/run.sh ${WDIR}/srv/TaskManager/

# for debuggin purpose
RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-crab3

# make sure all /data own by running user
RUN chown -R 1000:1000 /data

## add github script
=======
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
>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))
#COPY --chown=${USER}:${USER} addGH.sh ./
## add GitHub repositories
#RUN ./addGH.sh

<<<<<<< HEAD
=======
# clean up
RUN rm -rf /build

WORKDIR /data
>>>>>>> e1694450 (copy from poc branch (wmcore_pypi))
USER ${USER}

ENTRYPOINT ["tini", "--"]
CMD bash
