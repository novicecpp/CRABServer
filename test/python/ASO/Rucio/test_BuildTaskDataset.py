import re
import pytest
import uuid
import datetime
from unittest.mock import patch, Mock
from rucio.common.exception import DataIdentifierAlreadyExists, InvalidObject, DuplicateRule

from ASO.Rucio.Actions.BuildTaskDataset import BuildTaskDataset

# import from regexps.py instead?
RX_BLOCK = re.compile(r"^(/[a-zA-Z0-9\.\-_]{1,100}){3}#[a-zA-Z0-9\.\-_]{1,100}$")

@pytest.fixture
def mock_Transfer():
    rucioScope = 'user.tseethon'
    publishname = '/testPrimary/testDataset/RAW'
    currentDataset = f'{publishname}#c9b28b96-5d16-41cd-89af-2678971132c9'
    logsDataset = f'{publishname}#LOG'
    return Mock(publishname=publishname, currentDataset=currentDataset, rucioScope=rucioScope, logsDataset=logsDataset)


@pytest.fixture
def mock_rucioClient():
    with patch('rucio.client.client.Client', autospec=True) as new_callable:
        return new_callable

def test_createDataset_new_transfer_currentDataset(mock_rucioClient, mock_Transfer):
    previousDataset = mock_Transfer.currentDataset
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset()
    assert mock_Transfer.currentDataset != previousDataset
    assert RX_BLOCK.match(mock_Transfer.currentDataset)

def test_check_or_create_container_create_new_container(mock_rucioClient, mock_Transfer):
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.check_or_create_container()
    mock_rucioClient.add_container.assert_called_with(mock_Transfer.rucioScope, mock_Transfer.publishname)

def test_check_or_create_container_container_exist(mock_rucioClient, mock_Transfer):
    def mock_raise_DataIdentifierAlreadyExists():
        raise DataIdentifierAlreadyExists
    mock_Transfer.add_container = mock_raise_DataIdentifierAlreadyExists
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.check_or_create_container()

# test getOrCreateCurrentDataset()
# algo
# - list all dataset filter only open_ds and not LOG
# - if open_ds > 1: select [0] for now
# - if open_ds == 1 use [0]
# - if open_ds == 0: create new
# this assume we always have logs dataset in container before come to this function

def genContentAndMetadata(num, withLogsDataset=True):
    dataset = []
    datasetMetadata = []

    datasetTemplates = {
        'scope': 'user.cmsbot',
        'name': '/UserDataset/cmsbot-unittest-1/USER#{uuidStr}',
        'type': 'DATASET',
        'bytes': None,
        'adler32': None,
        'md5': None
    }
    datasetMetadataTemplate = {
        'scope': 'user.cmsbot',
        'name': '/UserDataset/cmsbot-unittest-1/USER#{uuidStr}',
        'account': 'tseethon',
        'did_type': 'DATASET',
        'is_open': False,
    }
    if withLogsDataset:
        uuidStr = str(uuid.uuid4())
        logDataset = datasetTemplates.copy()
        logDataset['name'] = logDataset['name'].format(uuidStr="LOG")
        dataset.append(logDataset)
        logDatasetMetadata = datasetMetadataTemplate.copy()
        logDatasetMetadata['name'] = logDataset['name'].format(uuidStr="LOG")
        logDatasetMetadata['is_open'] = True
        datasetMetadata.append(logDatasetMetadata)
    for i in range(num):
        uuidStr = str(uuid.uuid4())
        tmpDataset = datasetTemplates.copy()
        tmpDataset['name'] = tmpDataset['name'].format(uuidStr=uuidStr)
        dataset.append(tmpDataset)
        tmpDatasetMetadata = datasetMetadataTemplate.copy()
        tmpDatasetMetadata['name'] = tmpDataset['name'].format(uuidStr=uuidStr)
        tmpDatasetMetadata['is_open'] = False
        datasetMetadata.append(tmpDatasetMetadata)
    if num == 3:
        datasetMetadata[1]['is_open'] = True
    if num == 5:
        datasetMetadata[1]['is_open'] = True
        datasetMetadata[3]['is_open'] = True
    return dataset, datasetMetadata


def test_getOrCreateCurrentDataset_zero_dataset(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMedataContent = genContentAndMetadata(0)
    def mock_rucioClient_raise_InvalidObject():
        raise InvalidObject
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk = mock_rucioClient_raise_InvalidObject
    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.getOrCreateDataset()
    b.createDataset.assert_called_once_with()

def test_getOrCreateCurrentDataset_one_close_dataset(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMedataContent = genContentAndMetadata(1)
    def mock_rucioClient_raise_InvalidObject():
        raise InvalidObject
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk = mock_rucioClient_raise_InvalidObject
    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.getOrCreateDataset()
    b.createDataset.assert_called_once_with()

def test_getOrCreateCurrentDataset_one_open_dataset(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMedataContent = genContentAndMetadata(3)
    def mock_rucioClient_raise_InvalidObject():
        raise InvalidObject
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk = mock_rucioClient_raise_InvalidObject
    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
    previousDataset = mock_Transfer.currentDataset
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.getOrCreateDataset()
    b.createDataset.assert_not_called()
    assert mock_Transfer.currentDataset != previousDataset

def test_getOrCreateCurrentDataset_two_open_dataset(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMedataContent = genContentAndMetadata(5)
    def mock_rucioClient_raise_InvalidObject():
        raise InvalidObject
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk = mock_rucioClient_raise_InvalidObject
    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
    previousDataset = mock_Transfer.currentDataset
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.getOrCreateDataset()
    b.createDataset.assert_not_called()
    assert mock_Transfer.currentDataset != previousDataset

def test_createLogsDataset_logs_dataset_does_not_exist(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMedataContent = genContentAndMetadata(5, withLogsDataset=False)
    mock_rucioClient.list_content.return_value = datasetContent
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.createLogsDataset()
    datasetName = f'{mock_Transfer.publishname}#LOG'
    b.createDataset.assert_called_with(mock_Transfer.rucioScope, datasetName, mock_Transfer.publishname)


def test_createLogsDataset_logs_dataset_exist(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMedataContent = genContentAndMetadata(5)
    mock_rucioClient.list_content.return_value = datasetContent
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.createLogsDataset()
    datasetName = f'{mock_Transfer.publishname}#LOG'
    b.createDataset.assert_called_with(mock_Transfer.rucioScope, datasetName, mock_Transfer.publishname)
