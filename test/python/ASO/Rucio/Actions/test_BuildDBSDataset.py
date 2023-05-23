import re
import pytest
import uuid
import datetime
import json
from unittest.mock import patch, Mock
from ASO.Rucio.exception import RucioTransferException
from rucio.common.exception import DataIdentifierAlreadyExists, InvalidObject, DuplicateRule, DuplicateContent

from ASO.Rucio.Actions.BuildDBSDataset import BuildDBSDataset

# FIXME: class name is changed from BuildDBSDataset to BuildDBSDataset.
# Need to fix on all test in this files

@pytest.fixture
def mock_Transfer():
    transferObj = Mock()
    transferObj.rucioScope = f'user.cmscrab'
    transferObj.publishContainer = '/TestPrimary/test-dataset/USER'
    transferObj.currentPublishDataset = f'{transferObj.publishContainer}#c9b28b96-5d16-41cd-89af-2678971132c9'
    transferObj.transferContainer = '/TestPrimary/test-dataset_TRANSFER-bc8b2558/USER'
    transferObj.currentTransferDataset = f'{transferObj.transferContainer}#c9b28b96-5d16-41cd-89af-26789711abcd'
    transferObj.logsDataset = f'{transferObj.currentTransferDataset}#LOG'
    return transferObj

@pytest.fixture
def mock_rucioClient():
    with patch('rucio.client.client.Client', autospec=True) as m_rucioClient:
        return m_rucioClient

@pytest.fixture
def loadDatasetContent():
    with open('test/assets/dataset_content.json') as r:
        return json.load(r)

@pytest.fixture
def loadDatasetMetadata():
    with open('test/assets/dataset_metadata.json') as r:
        return json.load(r)

def test_checkOrCreateContainer_create_new_container(mock_rucioClient, mock_Transfer):
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    containerName = 'testContainer'
    b.checkOrCreateContainer(containerName)
    mock_rucioClient.add_container.assert_called_with(mock_Transfer.rucioScope, containerName)

def test_checkOrCreateContainer_container_exist(mock_rucioClient, mock_Transfer):
    def mock_raise_DataIdentifierAlreadyExists():
        raise DataIdentifierAlreadyExists
    mock_Transfer.add_container = mock_raise_DataIdentifierAlreadyExists
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    containerName = 'testContainer'
    b.checkOrCreateContainer(containerName)


# NOTE:
# 1) unittest still pass when you get data from self instead of param
#    how do we check that?
# 2) we did not check if params parse to rucioClient function correctly,
#    should we do it in integration test or in unittest?

def test_createDataset(mock_Transfer, mock_rucioClient):
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    b.createDataset(mock_Transfer.transferContainer, mock_Transfer.currentTransferDataset)
    mock_rucioClient.add_dataset.assert_called_once_with(mock_Transfer.rucioScope, mock_Transfer.currentTransferDataset)
    mock_rucioClient.attach_dids.assert_called_once()
    callScope, callContainer, _ = mock_rucioClient.attach_dids.call_args.args
    assert callScope == mock_Transfer.rucioScope
    assert callContainer == mock_Transfer.transferContainer

@pytest.mark.parametrize('methodName,exception', [
    ('add_dataset', DataIdentifierAlreadyExists),
    ('attach_dids', DuplicateContent),
])
def test_createDataset_raise_exception(mock_Transfer, mock_rucioClient, methodName, exception):
    getattr(mock_rucioClient, methodName).side_effect = exception
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    b.createDataset(mock_Transfer.transferContainer, mock_Transfer.currentTransferDataset)
    mock_rucioClient.add_dataset.assert_called_once_with(mock_Transfer.rucioScope, mock_Transfer.currentTransferDataset)
    mock_rucioClient.attach_dids.assert_called_once()
    callScope, callContainer, _ = mock_rucioClient.attach_dids.call_args.args
    assert callScope == mock_Transfer.rucioScope
    assert callContainer == mock_Transfer.transferContainer

# test getOrCreateDataset()
# algo
# - list all dataset filter only open_ds and not LOG
# - if open_ds > 1: select [0] for now
# - if open_ds == 1 use [0]
# - if open_ds == 0: create new
# this assume we always have logs dataset in container before come to this function
#

def genContentAndMetadata(transfer, num, withLogsDataset=True):
    dataset = []
    datasetMetadata = []
    uuidStrList = [
        'c3800048-d946-45f7-9e83-1f420b4fc32e',
        'b74d9bde-9a36-4e40-af17-3d614f19d380',
        'b3b1428c-d1c1-48d6-b61f-546b42010625',
        'fb16200d-3eb7-46f2-a8e7-c0ba57b383fd',
        '8377371a-6ee5-4178-9577-d948f414f69a',
    ]

    datasetTemplates = {
        'scope': transfer.rucioScope,
        'name': f'{transfer.transferContainer}#{{uuidStr}}',
        'type': 'DATASET',
        'bytes': None,
        'adler32': None,
        'md5': None
    }
    datasetMetadataTemplate = {
        'scope': transfer.rucioScope,
        'name': f'{transfer.transferContainer}#{{uuidStr}}',
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
        tmpDataset = datasetTemplates.copy()
        tmpDataset['name'] = tmpDataset['name'].format(uuidStr=uuidStrList[i])
        dataset.append(tmpDataset)
        tmpDatasetMetadata = datasetMetadataTemplate.copy()
        tmpDatasetMetadata['name'] = tmpDataset['name'].format(uuidStr=uuidStrList[i])
        tmpDatasetMetadata['is_open'] = False
        datasetMetadata.append(tmpDatasetMetadata)
    return dataset, datasetMetadata

@pytest.mark.parametrize('nDataset', [0, 1, 5])
def test_getOrCreateDataset_new_dataset(mock_Transfer, mock_rucioClient, loadDatasetContent, loadDatasetMetadata, nDataset):
    datasetContent = loadDatasetContent[:nDataset+1]
    datasetMetadata = loadDatasetMetadata[:nDataset]
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk.side_effect = InvalidObject
    mock_rucioClient.get_metadata.side_effect = datasetMetadata
    uuidstr = '5b8794fb-fe8f-479b-b2f8-d2d76a8ca370'
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.generateDatasetName = Mock()
    newDatasetName = f'{mock_Transfer.transferContainer}#{uuidstr}'
    b.generateDatasetName.return_value = newDatasetName
    assert b.getOrCreateDataset(mock_Transfer.transferContainer) == newDatasetName
    b.createDataset.assert_called_once()


def test_getOrCreateDataset_one_open_dataset(mock_Transfer, mock_rucioClient, loadDatasetContent, loadDatasetMetadata):
    datasetContent = loadDatasetContent
    datasetMetadata = loadDatasetMetadata
    datasetMetadata[1]['is_open'] = True
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk.side_effect = InvalidObject
    mock_rucioClient.get_metadata.side_effect = datasetMetadata
    uuidstr = '5b8794fb-fe8f-479b-b2f8-d2d76a8ca370'
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.generateDatasetName = Mock()
    newDatasetName = f'{mock_Transfer.transferContainer}#{uuidstr}'
    b.generateDatasetName.return_value = newDatasetName
    assert b.getOrCreateDataset(mock_Transfer.transferContainer) == datasetMetadata[1]['name']
    b.createDataset.assert_called_once()


def test_getOrCreateDataset_two_open_dataset(mock_Transfer, mock_rucioClient, loadDatasetContent, loadDatasetMetadata):
    datasetContent = loadDatasetContent
    datasetMetadata = loadDatasetMetadata
    datasetMetadata[1]['is_open'] = True
    datasetMetadata[4]['is_open'] = True
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk.side_effect = InvalidObject
    mock_rucioClient.get_metadata.side_effect = datasetMetadata
    uuidstr = '5b8794fb-fe8f-479b-b2f8-d2d76a8ca370'
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    b.generateDatasetName = Mock()
    newDatasetName = f'{mock_Transfer.transferContainer}#{uuidstr}'
    b.generateDatasetName.return_value = newDatasetName
    assert b.getOrCreateDataset(mock_Transfer.transferContainer) == datasetMetadata[1]['name']
    b.createDataset.assert_called_once()


def test_createTransferContainer_add_rule(mock_Transfer, mock_rucioClient):
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    b.checkOrCreateContainer = Mock()
    ruleID = '4c7a5025378d420288b418017fc23f18'
    mock_Transfer.containerRuleID = ''
    mock_rucioClient.add_replication_rule.return_value = [ruleID]
    b.createTransferContainer(mock_Transfer.transferContainer)
    mock_rucioClient.add_replication_rule.assert_called_once()
    mock_rucioClient.list_did_rules.assert_not_called()
    mock_Transfer.updateContainerRuleID.assert_called_once_with(ruleID)

def test_createTransferContainer_add_duplicate(mock_Transfer, mock_rucioClient):
    b = BuildDBSDataset(mock_Transfer, mock_rucioClient)
    b.checkOrCreateContainer = Mock()
    ruleID = '4c7a5025378d420288b418017fc23f18'
    mock_Transfer.containerRuleID = ''
    mock_rucioClient.add_replication_rule.side_effect = DuplicateRule
    mock_rucioClient.list_did_rules.return_value = [{'id': ruleID}]
    b.createTransferContainer(mock_Transfer.transferContainer)
    # assert
    mock_rucioClient.add_replication_rule.assert_called_once()
    mock_rucioClient.list_did_rules.assert_called_once()
    mock_Transfer.updateContainerRuleID.assert_called_once_with(ruleID)

#def test_createTransferContainer_bookkeeping(mock_Transfer, mock_rucioClient):
