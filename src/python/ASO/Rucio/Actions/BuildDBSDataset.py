import logging
import uuid

from rucio.common.exception import DataIdentifierAlreadyExists, InvalidObject, DuplicateRule, DuplicateContent

from ASO.Rucio.exception import RucioTransferException

class BuildDBSDataset():
    """
    Create Rucio's container and dataset.

    :param transfer: Transfer Object to get infomation.
    :type object: class:`ASO.Rucio.Transfer`
    :param rucioClient: Rucio Client object.
    :type object: class:`rucio.client.client.Client`
    """
    def __init__(self, transfer, rucioClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.BuildDBSDataset")
        self.rucioClient = rucioClient
        self.transfer = transfer

    def execute(self):
        """
        Creating DBS Dataset by create a new Rucio container and add a LOGS datasets.
        """
        # create publishContainer
        self.checkOrCreateContainer(self.transfer.publishContainer)
        # create transfer container and create rule id
        self.createTransferContainer(self.transfer.transferContainer)
        # create log dataset
        self.createDataset(self.transfer.transferContainer, self.transfer.logsDataset)

    def checkOrCreateContainer(self, containerName):
        self.logger.debug(f'Creating container "{self.transfer.rucioScope}:{containerName}')
        try:
            self.rucioClient.add_container(self.transfer.rucioScope, containerName)
            self.logger.info(f"{containerName} container created")
        except DataIdentifierAlreadyExists:
            self.logger.info(f"{containerName} container already exists, doing nothing")
        except Exception as ex:
            raise RucioTransferException('Failed to create container') from ex

    def createTransferContainer(self, container):
        """
        Creating Rucio container for files transfer and add replication rule to
        it. Do nothing if container and rule are already created.

        :returns: None
        """

        self.checkOrCreateContainer(container)

        self.logger.debug(f'Add replication rule to container "{self.transfer.rucioScope}:{container}')
        if self.transfer.containerRuleID:
            self.logger.info("Rule already exists, doing nothing")
        else:
            try:
                containerDID = {
                    'scope': self.transfer.rucioScope,
                    'name': container,
                    'type': "CONTAINER",
                }
                ruleID = self.rucioClient.add_replication_rule([containerDID], 1, self.transfer.destination)[0]
                # TODO: not sure if any other case make the rule duplicate beside script crash
            except DuplicateRule:
                # TODO: it possible that someone will create the rule for container, need better filter rule to match rules we create
                self.logger.info(f"Rule already exists. Get rule ID from Rucio.")
                ruleID = list(self.rucioClient.list_did_rules(self.transfer.rucioScope, container))[0]['id']
            self.transfer.updateContainerRuleID(ruleID)

    def getOrCreateDataset(self, containerName):
        """
        Get or create new dataset.
        - If open more than 2, choose one and close other.
        - If only one is open, go ahead and use it.
        - if none, create new one.
        Note that this method always call createDataset() to ensure that datasets
        are attached to container.

        :returns: dataset name
        :rtype: str
        """

        datasets = self.rucioClient.list_content(self.transfer.rucioScope, containerName)
        # remove log dataset
        datasets = [ds for ds in datasets if not ds['name'].endswith('#LOGS')]
        self.logger.debug(f"datasets in container: {datasets}")

        # get_metadata_bulk "Always" raise InvalidObject.
        # Probably a bug on rucio server, even production block.
        try:
            metadata = self.rucioClient.get_metadata_bulk(datasets)
        except InvalidObject:
            # Cover the case for which the dataset has been created but has 0 files
            metadata = []
            for ds in datasets:
                metadata.append(self.rucioClient.get_metadata(self.transfer.rucioScope, ds["name"]))
        openDatasets = [md['name'] for md in metadata if md['is_open'] == True]
        self.logger.debug(f"open datasets: {datasets}")
        if len(openDatasets) == 0:
            self.logger.info("No dataset available yet, creating one")
            currentDatasetName = self.generateDatasetName(containerName)
        elif len(openDatasets) == 1:
            currentDatasetName = openDatasets[0]
            self.logger.info(f"Found exactly one open dataset: {currentDatasetName}")
        # which case we went through this?
        else:
            self.logger.info(
                "Found more than one open dataset, closing the one with more files and using the other as the current one")
            # TODO: close the most occupied and take the other as the current one -
            # so far we take the first and then let the Publisher close the dataset when task completed
            currentDatasetName = openDatasets[0]
        # always execute createDataset() again in case replication rule is not create and the dids is not attach to root container
        self.createDataset(containerName, currentDatasetName)
        return currentDatasetName

    def createDataset(self, containerName, datasetName):
        """
        Creating Rucio dataset, add replication rule, attach to container.
        Ignore error if it already done.

        :param datasetName: dataset name to create.
        :returns: None
        :raises RucioTransferException: wrapping generic Exception and add
            message.
        """
        self.logger.debug(f'Creating dataset {datasetName}')
        try:
            self.rucioClient.add_dataset(self.transfer.rucioScope, datasetName)
        except DataIdentifierAlreadyExists:
            self.logger.info(f"{datasetName} dataset already exists, doing nothing")
        dsDID = {'scope': self.transfer.rucioScope, 'type': "DATASET", 'name': datasetName}
        try:
        # attach dataset to the container
            self.rucioClient.attach_dids(self.transfer.rucioScope, containerName, [dsDID])
        except DuplicateContent:
            self.logger.info(f'{datasetName} dataset has attached to {containerName}, doing nothing')

    def generateDatasetName(self, containerName):
        """
        Return a new dataset name.

        :returns: string of dataset name.
        """
        return f'{containerName}#{uuid.uuid4()}'
