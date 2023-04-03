import logging
import uuid

from rucio.common.exception import DataIdentifierAlreadyExists, InvalidObject, DuplicateRule

from ASO.Rucio.exception import RucioTransferException
from ASO.Rucio.config import config

class BuildTaskDataset():
    def __init__(self, transfer, rucioClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.BuildTaskDataset")
        self.rucioClient = rucioClient
        self.transfer = transfer

    def execute(self):
        # TODO: REFACTORING: refactoring these two function
        # load transfer.rucio_scope, and transfer.publishname
        self.check_or_create_container()
        self.check_or_create_current_dataset()

    def check_or_create_container(self):
        """
        creating container
         - check if container already exists
         - otherwise create it
        """
        try:
            self.rucioClient.add_container(self.transfer.rucioScope, self.transfer.publishname)
            self.logger.info(f"{self.transfer.publishname} container created")
        except DataIdentifierAlreadyExists:
            self.logger.info(f"{self.transfer.publishname} container already exists, doing nothing")
        except Exception as ex:
            raise RucioTransferException('Failed to create container') from ex

    def check_or_create_current_dataset(self, force_create=False):
        # Check if there are open datasets and then start from there:
        # - if open with less than max file go ahead and use it
        # - if max file is reached, close the currente ds and open a new one
        # - if force_create = True, create a new one anyway

        # TODO: create #LOGS dataset if does not exists
        # Can we simply avoid transferring LOGS with RUCIO?
        if not force_create:
            try:
                datasets = self.rucioClient.list_content(
                    self.transfer.rucioScope, self.transfer.publishname)
            except Exception as ex:
                raise RucioTransferException("Failed to list container content") from ex
            # get open datasets
            # if more than one, close the most occupied
            open_ds = []
            dids = []
            logs_ds_exists = False
            for d in datasets:
                if d['name'] == self.transfer.logsDataset:
                    self.logger.debug(f'Found LOG dataset: {d["name"]}')
                    logs_ds_exists = True
                dids.append(d)
            # If a ds for logs does not exists, create one
            if not logs_ds_exists:
                self.logger.debug(f'Creating LOG dataset {self.transfer.logsDataset}')
                try:
                    self.rucioClient.add_dataset(self.transfer.rucioScope, self.transfer.logsDataset)
                except DataIdentifierAlreadyExists:
                    self.logger.info(f"{self.transfer.publishname} log dataset already exists, doing nothing")
                try:
                    ds_did = {'scope': self.transfer.rucioScope, 'type': "DATASET", 'name': self.transfer.logsDataset}
                    self.rucioClient.add_replication_rule([ds_did], 1, self.transfer.destination)
                # TODO: not sure if any other case make the rule duplicate beside script crash
                except DuplicateRule:
                    self.logger.info(f"Rule already exists, doing nothing")
                try:
                    # attach dataset to the container
                    self.rucioClient.attach_dids(self.transfer.rucioScope, self.transfer.publishname, [ds_did])
                except Exception as ex:
                    raise RucioTransferException("Failed to create and attach a logs RUCIO dataset") from ex
            if len(dids) > 0:
                try:
                    metadata = self.rucioClient.get_metadata_bulk(dids)
                except InvalidObject:
                    # Cover the case for which the dataset has been created but has 0 files
                    # FIX: probably a bug on get_metadata_bulk that crash if any of the did has size 0
                    metadata = []
                    for did in dids:
                        metadata.append(self.rucioClient.get_metadata(
                            self.transfer.rucioScope, did["name"]))
                except Exception as ex:
                    raise RucioTransferException("Failed to get metadata in bulk for dids") from ex
                for md in metadata:
                    if md["is_open"]:
                        open_ds.append(md["name"])
            if len(open_ds) == 0:
                self.logger.info("No dataset available yet, creating one")
                self.createDataset()
            elif len(open_ds) > 1:
                self.logger.info(
                    "Found more than one open dataset, closing the one with more files and using the other as the current one")
                # TODO: close the most occupied and take the other as the current one -
                # so far we take the first and then let the Publisher close the dataset when task completed
                self.transfer.currentDataset = open_ds[0]
            elif len(open_ds) == 1:
                self.logger.info(f"Found exactly one open dataset, setting it as the current dataset: {open_ds[0]}")
                self.transfer.currentDataset = open_ds[0]
        else:
            self.logger.info("Forced creation of a new dataset.")
            self.createDataset()


    def createDataset(self):
        self.transfer.currentDataset = f"{self.transfer.publishname}#{uuid.uuid4()}"
        # create a new dataset
        # TODO: REFACTORING: merge with force_create = false
        try:
            self.rucioClient.add_dataset(self.transfer.rucioScope, self.transfer.currentDataset)
            ds_did = {'scope': self.transfer.rucioScope,
                      'type': "DATASET", 'name': self.transfer.currentDataset}
            self.rucioClient.add_replication_rule([ds_did], 1, self.transfer.destination)
            # attach dataset to the container
            self.rucioClient.attach_dids(self.transfer.rucioScope, self.transfer.publishname, [ds_did])
        except Exception as ex:
            raise RucioTransferException("Failed to create and attach a new RUCIO dataset") from ex
