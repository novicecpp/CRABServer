FROM registry.cern.ch/cmscrab/crabtaskworker:latest

# start image
FROM registry.cern.ch/cmsweb/wmagent-base:pypi-20230705
SHELL ["/bin/bash", "-c"]
ENV USER=crab3
ENV WDIR=/data

# install gfal
# symlink to workaround calling gfal from absolute path
COPY --from=wmcore-gfal ${WDIR}/miniconda ${WDIR}/miniconda
RUN ln -sf ${WDIR}/miniconda/bin/gfal-ls /usr/bin/gfal-ls \
    && ln -sf ${WDIR}/miniconda/bin/gfal-rm /usr/bin/gfal-rm \
    && ln -sf ${WDIR}/miniconda/bin/gfal-copy /usr/bin/gfal-copy \
    && ln -sf ${WDIR}/miniconda/bin/gfal-sum /usr/bin/gfal-sum

# install package from debian repository
# deps for openldap: libsasl2-dev python3-dev libldap-dev libssl-dev
RUN apt-get update \
    && apt-get install -y tini git zip voms-clients-java fd-find ripgrep libsasl2-dev python3-dev libldap-dev libssl-dev \
    && apt-get clean all

# local timezone (hardcode)
RUN ln -sf /usr/share/zoneinfo/Europe/Zurich /etc/localtime

# prepare build
RUN mkdir /build
WORKDIR /build

# install dependencies
COPY --from=wmcore-src /wmcore_version .
COPY cicd/crabtaskworker_pypi/requirements.txt .
RUN pip install -r requirements.txt \
    && pip install --no-deps wmcore==$(cat wmcore_version) \
    && pip cache purge

# copy htcondor config
RUN mkdir /etc/condor
COPY cicd/crabtaskworker_pypi/condor_config /etc/condor/

# install crabserver
# will replace with pip later
COPY src/python/ ${WDIR}/srv/current/lib/python/site-packages/
# copy TaskManagerRun.tar.gz
COPY --from=build-data /build/data_files/data ${WDIR}/srv/current/lib/python/site-packages/data

# copy cern openldap config
COPY --from=cern-cc7 /etc/openldap /etc/openldap

# copy rucio config
RUN mkdir -p /opt/rucio/etc/
COPY cicd/crabtaskworker_pypi/rucio.cfg /opt/rucio/etc/

# add github repos, reuse script in crabserver_pypi
COPY cicd/crabserver_pypi/addGH.sh .
RUN bash addGH.sh

# clean up
WORKDIR ${WDIR}
RUN rm -rf /build

# add new user and switch to user
RUN useradd -m ${USER} \
    && install -o ${USER} -d ${WDIR}

# create working directory
RUN mkdir -p ${WDIR}/srv/tmp
## taskworker
RUN mkdir -p ${WDIR}/srv/TaskManager/current \
           ${WDIR}/srv/TaskManager/cfg \
           ${WDIR}/srv/TaskManager/logs
## publisher
RUN mkdir -p ${WDIR}/srv/Publisher/current \
           ${WDIR}/srv/Publisher/cfg \
           ${WDIR}/srv/Publisher/logs \
           ${WDIR}/srv/Publisher/PublisherFiles

# copy process executor scripts
## TaskWorker
COPY cicd/crabtaskworker_pypi/TaskWorker/start.sh \
     cicd/crabtaskworker_pypi/TaskWorker/env.sh \
     cicd/crabtaskworker_pypi/TaskWorker/stop.sh \
     cicd/crabtaskworker_pypi/TaskWorker/manage.sh \
     cicd/crabtaskworker_pypi/updateDatafiles.sh \
     ${WDIR}/srv/TaskManager/

COPY cicd/crabtaskworker_pypi/bin/crab-taskworker /usr/local/bin/crab-taskworker

## publisher
COPY cicd/crabtaskworker_pypi/Publisher/start.sh \
     cicd/crabtaskworker_pypi/Publisher/env.sh \
     cicd/crabtaskworker_pypi/Publisher/stop.sh \
     cicd/crabtaskworker_pypi/Publisher/manage.sh \
     ${WDIR}/srv/Publisher/

## entrypoint
COPY cicd/crabtaskworker_pypi/run.sh /data

# for debuggin purpose
RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-crab3

# make sure all /data own by running user
# RUN chown -R 1000:1000 ${WDIR}

USER ${USER}

ENTRYPOINT ["tini", "--"]
CMD ["/data/run.sh"]
