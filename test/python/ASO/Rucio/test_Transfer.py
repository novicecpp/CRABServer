# should test detect provided wrong path to open function?

import pytest
import builtins
import json
from unittest.mock import patch, mock_open
from argparse import Namespace

from ASO.Rucio.Transfer import Transfer
from ASO.Rucio.exception import RucioTransferException
import ASO.Rucio.config as config


@pytest.fixture
def transfersTxtContent():
    path = 'test/assets/transfers.txt'
    with open(path, 'r', encoding='utf-8') as r:
        return r.read()

@pytest.fixture
def restInfoForFileTransfersJsonContent():
    path = 'test/assets/RestInfoForFileTransfers.json'
    with open(path, 'r', encoding='utf-8') as r:
        return r.read()



def test_Transfer_readInfo():
    restInfoForFileTransfersJson = {
        "host": "cmsweb-test12.cern.ch:8443",
        "dbInstance": "devthree",
        "proxyfile": "9041f6500ff40aaca33737316a2dbfb57116e8e0"
    }
    transfersTxt = {
        "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
        "username": "tseethon",
        "taskname": "230324_151740:tseethon_crab_rucio_transfer_whitelist_cern_test12_20230324_161736",
        "start_time": 1679671544,
        "destination": "T2_CH_CERN",
        "destination_lfn": "/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root",
        "source": "T2_CH_CERN",
        "source_lfn": "/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root",
        "filesize": 628054,
        "publish": 0,
        "transfer_state": "NEW",
        "publication_state": "NOT_REQUIRED",
        "job_id": "9",
        "job_retry_count": 0,
        "type": "output",
        "publishname": "autotest-1679671056-00000000000000000000000000000000",
        "checksums": {"adler32": "812b8235", "cksum": "1236675270"},
        "outputdataset": "/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER"
    }
    config.config = Namespace(force_publishname=None, rest_info_path='/a/b/c', transfer_info_path='/d/e/f')
    with patch('builtins.open', new_callable=mock_open, read_data=f'{json.dumps(restInfoForFileTransfersJson)}\n') as mo:
        # setup config
        mo.side_effect = (mo.return_value, mock_open(read_data=f'{json.dumps(transfersTxt)}\n').return_value,)
        # run config
        t = Transfer()
        t.readInfo()
        assert t.proxypath == '9041f6500ff40aaca33737316a2dbfb57116e8e0'
        assert t.username == 'tseethon'
        assert t.rucioScope == 'user.tseethon'
        assert t.destination == 'T2_CH_CERN'
        assert t.publishname == '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER'
        assert t.logsDataset == '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#LOGS'
        assert t.currentDataset == ''


def test_Transfer_readInfo_filenotfound():
    # setup config

    # run transfer
    config.config = Namespace(rest_info_path='/a/b/c', transfer_info_path='/d/e/f')
    t = Transfer()
    with pytest.raises(RucioTransferException):
        t.readInfo()

def test_readInfoFromTransferItems():
    transfersTxt = {
        "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
        "username": "tseethon",
        "taskname": "230324_151740:tseethon_crab_rucio_transfer_whitelist_cern_test12_20230324_161736",
        "start_time": 1679671544,
        "destination": "T2_CH_CERN",
        "destination_lfn": "/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root",
        "source": "T2_CH_CERN",
        "source_lfn": "/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root",
        "filesize": 628054,
        "publish": 0,
        "transfer_state": "NEW",
        "publication_state": "NOT_REQUIRED",
        "job_id": "9",
        "job_retry_count": 0,
        "type": "output",
        "publishname": "autotest-1679671056-00000000000000000000000000000000",
        "checksums": {"adler32": "812b8235", "cksum": "1236675270"},
        "outputdataset": "/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER"
    }
    t = Transfer()
    t.transferItem = [transfersTxt]
    t.readInfoFromTransferItems()
    assert t.username == 'tseethon'
    assert t.rucioScope == 'user.tseethon'
    assert t.destination == 'T2_CH_CERN'
    assert t.publishname == '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER'
    assert t.logsDataset == '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#LOGS'
    assert t.currentDataset == ''


def test_readRESTInfo():
    t = Transfer()
    t.lastTransferLine = 0
    config.config = Namespace(rest_info_path='/path/to/RestInfoForFileTransfers.json')
    with patch('ASO.Rucio.Transfer.open', new_callable=mock_open, read_data=restInfoForFileTransfersJsonContent) as mo:
        t.readTransferItems()
        assert mo.call_args.args[0] == '/path/to/RestInfoForFileTransfers.json'
        assert t.restHost == "cmsweb-test12.cern.ch:8443"
        assert t.restDBinstance == 'devthree'
        assert t.restProxyFile == '9041f6500ff40aaca33737316a2dbfb57116e8e0'


def test_readTransferItems_zero(transfersTxtContent):
    t = Transfer()
    t.lastTransferLine = 0
    with patch('builtins.open', new_callable=mock_open, read_data=transfersTxtContent) as mo:
        t.readTransferItems()
        assert  t.transferItems[5]['id'] == '5b5c6d9f2e99ae32191e2c702ca9bba32951d69027289a7cde884468'

def test_readTransferItems_start_at_line_six():
    t = Transfer()
    t.lastTransferLine = 5
    with patch('builtins.open', new_callable=mock_open, read_data=transfersTxtContent) as mo:
        t.readTransferItems()
        assert  t.transferItems[0]['id'] == '5b5c6d9f2e99ae32191e2c702ca9bba32951d69027289a7cde884468'


@pytest.mark.skip(reason="Skip it for now due deadline")
def test_readTransferItems_lastTransferLine_is_None():
    t = Transfer()
    with pytest.raises(RucioTransferException):
        t.readTransferItem()

@pytest.mark.skip(reason="Skip it for now due deadline")
def test_readTransferItems_no_new_item():
    t = Transfer()
    t.lastTransferLine = 20
    with pytest.raises(RucioTransferException):
        t.readTransferItem()

def test_readLastTransferLine():
    with patch('builtins.open', new_callable=mock_open, read_data='5\n') as mo:
        t = Transfer()
        t.readLastTransferLine()
        assert t.lastTransferLine == 5

def test_readLastTransferLine_file_not_found():
    config.config = Namespace(last_line_path='/a/b/c')
    t = Transfer()
    t.readLastTransferLine()
    assert t.lastTransferLine == 5

# do we need to test this thing?
# ======================
# if not os.path.exists('task_process/transfers'):
#     os.makedirs('task_process/transfers')
