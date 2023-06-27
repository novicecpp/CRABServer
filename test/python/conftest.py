from unittest.mock import Mock
import pytest


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
