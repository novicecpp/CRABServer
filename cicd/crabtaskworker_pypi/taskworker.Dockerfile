# caching wmcore src, need for building TaskManagerRun.tar.gz
FROM python:3.8 as wmcore-src
SHELL ["/bin/bash", "-c"]
# Use the "magic" requirements.txt from crabserver pypi
COPY cicd/crabserver_pypi/ .
RUN wmcore_repo="$(grep -v '^\s*#' wmcore_requirements.txt | cut -d' ' -f1)" \
    && wmcore_version="$(grep -v '^\s*#' wmcore_requirements.txt | cut -d' ' -f2)" \
    && git clone ${wmcore_repo} -b "${wmcore_version}" /WMCore \
    && ( cd /WMCore; git status ) \
    && echo "${wmcore_version}" > /wmcore_version

# start image
FROM base-image

# copy TaskManagerRun.tar.gz
COPY --from=build-data /build/data_files/data ${WDIR}/srv/current/lib/python/site-packages/data

# install crabserver
# will replace with pip later
COPY src/python/ ${WDIR}/srv/current/lib/python/site-packages/

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

# for debugging purpose
RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-crab3

# ensure all /data owned by running user
RUN chown -R 1000:1000 ${WDIR}

USER ${USER}

ENTRYPOINT ["tini", "--"]
CMD ["/data/run.sh"]