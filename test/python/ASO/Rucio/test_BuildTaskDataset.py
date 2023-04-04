import re
import pytest
import uuid
import datetime
from unittest.mock import patch, Mock
from ASO.Rucio.exception import RucioTransferException
from rucio.common.exception import DataIdentifierAlreadyExists, InvalidObject, DuplicateRule

from ASO.Rucio.Actions.BuildTaskDataset import BuildTaskDataset

@pytest.fixture
def mock_Transfer():
    username = 'cmscrab'
    rucioScope = f'user.{username}'
    publishname = '/TestPrimary/test-dataset/RAW'
    currentDatasetUUID = 'c9b28b96-5d16-41cd-89af-2678971132c9'
    currentDataset = f'{publishname}#{currentDatasetUUID}'
    logsDataset = f'{publishname}#LOG'
    return Mock(publishname=publishname, currentDataset=currentDataset, rucioScope=rucioScope, logsDataset=logsDataset, currentDatasetUUID=currentDatasetUUID, username=username)


@pytest.fixture
def mock_rucioClient():
    with patch('rucio.client.client.Client', autospec=True) as m_rucioClient:
        return m_rucioClient

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


def test_createDataset(mock_Transfer, mock_rucioClient):
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset(mock_Transfer.rucioScope, mock_Transfer.datasetName, mock_Transfer.publishname)
    mock_rucioClient.add_dataset.assert_called_once()
    mock_rucioClient.add_replication_rule.assert_called_once()
    mock_rucioClient.attach_dids.assert_called_once()

@pytest.mark.parametrize('methodName,exception', [
    ('add_dataset', DataIdentifierAlreadyExists),
    ('add_replication_rule', DuplicateRule),
    ('attach_dids', Exception),
])
def test_createDataset_raise_exception(mock_Transfer, mock_rucioClient, methodName, exception):
    getattr(mock_rucioClient, methodName).side_effect = exception
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset(mock_Transfer.rucioScope, mock_Transfer.datasetName, mock_Transfer.publishname)
    # too lazy to check args. maybe it should
    mock_rucioClient.add_dataset.assert_called_once()
    mock_rucioClient.add_replication_rule.assert_called_once()
    mock_rucioClient.attach_dids.assert_called_once()


# test getOrCreateDataset()
# algo
# - list all dataset filter only open_ds and not LOG
# - if open_ds > 1: select [0] for now
# - if open_ds == 1 use [0]
# - if open_ds == 0: create new
# this assume we always have logs dataset in container before come to this function

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
        'name': f'{transfer.publishname}#{{uuidStr}}',
        'type': 'DATASET',
        'bytes': None,
        'adler32': None,
        'md5': None
    }
    datasetMetadataTemplate = {
        'scope': transfer.rucioScope,
        'name': f'{transfer.publishname}#{{uuidStr}}',
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
def test_getOrCreateDataset_new_dataset(mock_Transfer, mock_rucioClient, nDataset):
    datasetContent, datasetMedataContent = genContentAndMetadata(mock_Transfer, nDataset)
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk.side_effect = InvalidObject
    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    newDatasetName = f'{mock_Transfer.publishname}#{mock_Transfer.currentDatasetUUID}'
    with patch('uuid.uuid4', autospec=True) as mock_uuid4:
        mock_uuid4.return_value = uuid.UUID(mock_Transfer.currentDatasetUUID)
        ret = b.getOrCreateDataset()
    assert ret == newDatasetName
    b.createDataset.assert_called_once_with(mock_Transfer.rucioScope, newDatasetName, mock_Transfer.publishname)


def test_getOrCreateDataset_one_open_dataset(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMetadataContent = genContentAndMetadata(mock_Transfer, 5)
    datasetMetadataContent[1]['is_open'] = True
    def mock_get_metadata(scope, name):
        for i in datasetMetadataContent:
            if i['name'] == name:
                return i
        return None
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk.side_effect = InvalidObject
    mock_rucioClient.get_metadata.side_effect = mock_get_metadata
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    newDatasetName = f'{datasetContent[1]["name"]}'
    assert b.getOrCreateDataset() == newDatasetName
    b.createDataset.assert_called_once_with(mock_Transfer.rucioScope, newDatasetName, mock_Transfer.publishname)



def test_getOrCreateDataset_two_open_dataset(mock_Transfer, mock_rucioClient):
    datasetContent, datasetMetadataContent = genContentAndMetadata(mock_Transfer, 5)
    datasetMetadataContent[1]['is_open'] = True
    datasetMetadataContent[4]['is_open'] = True
    mock_rucioClient.list_content.return_value = datasetContent
    # we cannot use get_metadata_bulk right now because even recent dataset,
    # bytes from rucioClient.list_client still None
    mock_rucioClient.get_metadata_bulk.side_effect = InvalidObject
    mock_rucioClient.get_metadata.side_effect = tuple(datasetMetadataContent)
    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
    b.createDataset = Mock()
    newDatasetName = f'{datasetContent[1]["name"]}'
    assert b.getOrCreateDataset() == newDatasetName
    b.createDataset.assert_called_once_with(mock_Transfer.rucioScope, newDatasetName, mock_Transfer.publishname)






#def test_getOrCreateCurrentDataset_close_dataset(mock_Transfer, mock_rucioClient):
#    datasetContent, datasetMedataContent = genContentAndMetadata(5)
#    def mock_rucioClient_raise_InvalidObject():
#        raise InvalidObject
#    mock_rucioClient.list_content.return_value = datasetContent
#    # we cannot use get_metadata_bulk right now because even recent dataset,
#    # bytes from rucioClient.list_client still None
#    mock_rucioClient.get_metadata_bulk = mock_rucioClient_raise_InvalidObject
#    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
#    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
#    b.createDataset = Mock()
#    b.getOrCreateDataset()
#    datasetName = f'{mock_Transfer.publishname}#8fa92764-63c5-4825-ade8-4684288bf984'
#    with patch('uuid.uuid4', autospec=True) as mock_uuid4:
#        mock_uuid4.return_value = uuid.UUID('8fa92764-63c5-4825-ade8-4684288bf984')
#        b.createDataset.assert_called_with(mock_Transfer.rucioScope, datasetName, mock_Transfer.publishname)
#
#
#
#
#
#
#
#
#
#
#
#
#def test_getOrCreateDataset_one_open_dataset(mock_Transfer, mock_rucioClient):
#    datasetContent, datasetMedataContent = genContentAndMetadata(3)
#    def mock_rucioClient_raise_InvalidObject():
#        raise InvalidObject
#    mock_rucioClient.list_content.return_value = datasetContent
#    # we cannot use get_metadata_bulk right now because even recent dataset,
#    # bytes from rucioClient.list_client still None
#    mock_rucioClient.get_metadata_bulk = mock_rucioClient_raise_InvalidObject
#    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
#    previousDataset = mock_Transfer.currentDataset
#    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
#    b.createDataset = Mock()
#    b.getOrCreateDataset()
#    b.createDataset.assert_called_once_with()
#    assert mock_Transfer.currentDataset != previousDataset
#
#def test_getOrCreateCurrentDataset_two_open_dataset(mock_Transfer, mock_rucioClient):
#    datasetContent, datasetMedataContent = genContentAndMetadata(5)
#    def mock_rucioClient_raise_InvalidObject():
#        raise InvalidObject
#    mock_rucioClient.list_content.return_value = datasetContent
#    # we cannot use get_metadata_bulk right now because even recent dataset,
#    # bytes from rucioClient.list_client still None
#    mock_rucioClient.get_metadata_bulk = mock_rucioClient_raise_InvalidObject
#    mock_rucioClient.get_metadata.side_effect = tuple(datasetMedataContent)
#    previousDataset = mock_Transfer.currentDataset
#    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
#    b.createDataset = Mock()
#    b.getOrCreateDataset()
#    b.createDataset.assert_not_called()
#    assert mock_Transfer.currentDataset != previousDataset
#
#
#def test_createLogsDataset_logs_dataset_does_not_exist(mock_Transfer, mock_rucioClient):
#    datasetContent, datasetMedataContent = genContentAndMetadata(5, withLogsDataset=False)
#    mock_rucioClient.list_content.return_value = datasetContent
#    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
#    b.createDataset = Mock()
#    b.createLogsDataset()
#    datasetName = f'{mock_Transfer.publishname}#LOG'
#    b.createDataset.assert_called_with(mock_Transfer.rucioScope, datasetName, mock_Transfer.publishname)
#
#
#def test_createLogsDataset_logs_dataset_exist(mock_Transfer, mock_rucioClient):
#    datasetContent, datasetMedataContent = genContentAndMetadata(5)
#    mock_rucioClient.list_content.return_value = datasetContent
#    b = BuildTaskDataset(mock_Transfer, mock_rucioClient)
#    b.createDataset = Mock()
#    b.createLogsDataset()
#    datasetName = f'{mock_Transfer.publishname}#LOG'
#    b.createDataset.assert_called_with(mock_Transfer.rucioScope, datasetName, mock_Transfer.publishname)
