# monitor_locks_status get list of dataset from list_content() api from publishname
# FOR EACH dataset, get rules name
# ================================
#
# for source of truth (input), get it from bookkeeping file. not passing down
# in memory from register replicas because register replicas already skip some
# entry.
# maybe do it at top
# input is something like {ruleID1: datasetName1, ruleID2: datasetName2}
# outputs are
# 1. replicas state is ok: same as ReegisterReplicas.register(), but plus blockCompletes for rule state is ok
# 2. replicas state is replication: need rule id and id (no need for dataset)
import json
import pytest
import datetime
from argparse import Namespace
from unittest.mock import patch, Mock, call

import ASO.Rucio.config as config
from ASO.Rucio.Actions.MonitorLocksStatus import MonitorLocksStatus
from ASO.Rucio.Actions.RegisterReplicas import RegisterReplicas

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

@pytest.fixture
def loadDatasetMetadata():
    with open('test/assets/dataset_metadata.json') as r:
        return json.load(r)

@pytest.fixture
def LFN2transferItemMap():
    with open('test/assets/LFN2transferItemMap.json') as r:
        return json.load(r)

def test_checkLockStatus_all_ok(mock_Transfer, mock_rucioClient):
    listRuleIDs = ['b43a554244c54dba954aa29cb2fdde0a']
    outputAllOK = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#c9b28b96-5d16-41cd-89af-2678971132c9',
            "blockcomplete": 'OK',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        }
    ]
    listReplicaLocksReturnValue = [{
        'name': '/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root',
        'state': 'OK',
    }]

    mock_rucioClient.list_replica_locks.side_effect = ((x for x in listReplicaLocksReturnValue), ) # list_replica_locks return generator
    mock_Transfer.replicaLFN2IDMap = {
        '/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root' : '98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca'
    }
    mock_Transfer.replicasInContainer = {
        '/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root' : '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#c9b28b96-5d16-41cd-89af-2678971132c9'
    }
    mock_Transfer.containerRuleID = 'b43a554244c54dba954aa29cb2fdde0a'
    config.args = Namespace(max_file_per_dataset=1)
    m = MonitorLocksStatus(mock_Transfer, mock_rucioClient, Mock())
    assert m.checkLocksStatus() == (outputAllOK, [])

def test_checkLockStatus_all_replicating(mock_Transfer, mock_rucioClient):
    listRuleIDs = ['b43a554244c54dba954aa29cb2fdde0a']
    outputNotOK = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#c9b28b96-5d16-41cd-89af-2678971132c9',
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        }
    ]
    getReplicationRuleReturnValue = {
        'id': 'b43a554244c54dba954aa29cb2fdde0a',
        'name': '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#c9b28b96-5d16-41cd-89af-2678971132c9',
        'state': 'REPLICATING',
    }
    listReplicaLocksReturnValue = [{
        'name': '/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root',
        'state': 'REPLICATING',
    }]
    mock_rucioClient.get_replication_rule.return_value = getReplicationRuleReturnValue
    mock_rucioClient.list_replica_locks.side_effect = ((x for x in listReplicaLocksReturnValue), ) # list_replica_locks return generator
    mock_Transfer.getIDFromLFN.return_value = '98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca'
    m = MonitorLocksStatus(mock_Transfer, mock_rucioClient, Mock())
    assert m.checkLocksStatus(listRuleIDs) == ([], outputNotOK, [])

@pytest.mark.skip(reason="Skip it for now due deadline.")
def test_checkLockStatus_mix():
    assert True == False

# bookkeeping rule
# - bookkeeping per dataset
# - save rule id if rule ok to another file
@patch.object(MonitorLocksStatus, 'checkLocksStatus')
def test_execute_bookkeeping_none(mock_checkLockStatus, mock_Transfer):
    allRules = ['b43a554244c54dba954aa29cb2fdde0a']
    okRules = []
    mock_Transfer.allRules = allRules
    mock_Transfer.okRules = okRules
    m = MonitorLocksStatus(mock_Transfer, mock_rucioClient, Mock())
    mock_checkLockStatus.return_value = ([], [], okRules)
    m.execute()
    mock_checkLockStatus.assert_called_once_with(allRules)
    mock_Transfer.updateOKRules.assert_called_once()

@patch.object(MonitorLocksStatus, 'checkLocksStatus')
def test_execute_bookkeeping_all(mock_checkLockStatus, mock_Transfer):
    allRules = ['b43a554244c54dba954aa29cb2fdde0a']
    okRules = ['b43a554244c54dba954aa29cb2fdde0a']
    mock_Transfer.allRules = allRules
    mock_Transfer.okRules = okRules
    m = MonitorLocksStatus(mock_Transfer, mock_rucioClient, Mock())
    mock_checkLockStatus.return_value = ([], [], [])
    m.execute()
    mock_checkLockStatus.assert_called_once_with([])
    mock_Transfer.updateOKRules.assert_called_once()


def generateExpectedOutput(doctype):
    if doctype == 'complete':
        return {
            'asoworker': 'rucio',
            'list_of_ids': ['98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca'], # hmm, how do we get this
            'list_of_transfer_state': ['DONE'],
            'list_of_dbs_blockname': ['/TestDataset/cmscrab-unittest-1/USER#c9b28b96-5d16-41cd-89af-2678971132ca'],
            'list_of_block_complete': ['OK'],
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/'],
            'list_of_failure_reason': None, # omit
            'list_of_retry_value': None, # omit
            'list_of_fts_id': ['NA'],
        }
    elif doctype == 'notcomplete':
        return {
            'asoworker': 'rucio',
            'list_of_ids': ['98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cb'], # hmm, how do we get this
            'list_of_transfer_state': ['SUBMITTED'],
            'list_of_dbs_blockname': None,
            'list_of_block_complete': None,
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/'],
            'list_of_failure_reason': None, # omit
            'list_of_retry_value': None, # omit
            'list_of_fts_id': ['b43a554244c54dba954aa29cb2fdde0b'],
        }

def test_prepareOKFileDoc(mock_Transfer):
    okFileDoc = generateExpectedOutput('complete')
    outputOK = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": '/TestDataset/cmscrab-unittest-1/USER#c9b28b96-5d16-41cd-89af-2678971132ca',
            "blockcomplete": 'OK',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        }
    ]
    m = MonitorLocksStatus(mock_Transfer, Mock(), Mock())
    assert okFileDoc == m.prepareOKFileDoc(outputOK)


def test_prepareNotOKFileDoc(mock_Transfer):
    notOKFileDoc = generateExpectedOutput('notcomplete')
    outputNotOK = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cb",
            "dataset": '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#c9b28b96-5d16-41cd-89af-2678971132c9',
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0b",
        }
    ]
    m = MonitorLocksStatus(mock_Transfer, Mock(), Mock())
    assert notOKFileDoc == m.prepareNotOKFileDoc(outputNotOK)

def test_addReplicasToPublishContainer():
    outputOK = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": '/TestDataset/cmscrab-unittest-1/USER#c9b28b96-5d16-41cd-89af-2678971132ca',
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        }
    ]
    m = MonitorLocksStatus(mock_Transfer, mock_rucioClient, Mock())
    m.addReplicasToPublishContainer(outputOK)


@patch.object(RegisterReplicas, 'addReplicasToDataset')
def test_updateBlockCompleteStatus(mock_addReplicasToDataset, mock_Transfer, mock_rucioClient, loadDatasetMetadata):
    outputOK = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": None,
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cb",
            "dataset": None,
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cc",
            "dataset": None,
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
    ]
    retAddReplicasToDataset = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": '/TestPrimary/test-dataset_TRANSFER-bc8b2558/USER#c3800048-d946-45f7-9e83-1f420b4fc32e',
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cb",
            "dataset": '/TestPrimary/test-dataset_TRANSFER-bc8b2558/USER#c3800048-d946-45f7-9e83-1f420b4fc32e',
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cc",
            "dataset": '/TestPrimary/test-dataset_TRANSFER-bc8b2558/USER#b74d9bde-9a36-4e40-af17-3d614f19d380',
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
    ]
    expectedOutput = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": '/TestPrimary/test-dataset_TRANSFER-bc8b2558/USER#c3800048-d946-45f7-9e83-1f420b4fc32e',
            "blockcomplete": 'OK',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cb",
            "dataset": '/TestPrimary/test-dataset_TRANSFER-bc8b2558/USER#c3800048-d946-45f7-9e83-1f420b4fc32e',
            "blockcomplete": 'OK',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20cc",
            "dataset": '/TestPrimary/test-dataset_TRANSFER-bc8b2558/USER#b74d9bde-9a36-4e40-af17-3d614f19d380',
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
    ]

    def side_effect(*args):
        container = args[1]
        index = multiPubContainers.index(container)
        return [returnValue[index]]

    t = create_autospec(Transfer, instance=True)
    t.multiPubContainers = multiPubContainers
    mock_addReplicasToContainer.side_effect = side_effect
    m = MonitorLockStatus(t, Mock(), Mock())
    ret = m.registerToMutiPubContainers(outputAllOK)


    # check args pass to addReplicasToContainer()
    allcall = []
    for i in range(len(returnValue)):
        allcall.append(call([outputAllOK[i]], multiPubContainers[i]))
    mock_addReplicasToContainer.assert_has_calls(allcall, any_order=True)

    # check return value
    assert sorted(ret, key=lambda d: d['id']) == sorted(returnValue, key=lambda d: d['id'])


def test_checkBlockCompleteStatus():
    assert 1 == 0

def test_CleanUpTempArea_allSuccess(mock_rucioClient, LFN2transferItemMap):
    t = create_autospec(Transfer, instance=True)
    # input1
    # input2 fileDocs
    # return nothing but have log.
    # mock subprocess.run
    LFN2PFNMap = {
        'T2_CH_CERN_Temp': {
            '/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/log/cmsRun_3.log.tar.gz': 'davs://eoscms.cern.ch:443/eos/cms/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/log/cmsRun_3.log.tar.gz',
            '/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/miniaodfake_3.root': 'davs://eoscms.cern.ch:443/eos/cms/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/miniaodfake_3.root',
            '/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/output_3.root': 'davs://eoscms.cern.ch:443/eos/cms/store/temp/user/tseethon.d6830fc3715ee01030105e83b81ff3068df7c8e0/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/output_3.root',
        }
    }
    fileDocs = [
        {
            "id": "7652449e07afeaf00abe804e8507f4172e5b04f09a2c5e0d883a3193",
            "name": "/store/user/rucio/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/log/cmsRun_3.log.tar.gz",
            "dataset": None,
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "10ba0d321da1a9d7ecc17e2bf411932ec5268ae12d5be76b5928dc29",
            "name": "/store/user/rucio/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/miniaodfake_3.root",
            "dataset": None,
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
        {
            "id": "091bfc9fb03fe326b1ace7cac5b71e034ce4b44ed46be14ae88b472a",
            "name": "/store/user/rucio/tseethon/test-rucio/ruciotransfers-1697125324/GenericTTbar/ruciotransfers-1697125324/231012_154207/0000/output_3.root",
            "dataset": None,
            "blockcomplete": 'NO',
            "ruleid": "b43a554244c54dba954aa29cb2fdde0a",
        },
    ]

    t.LFN2PFNMap = LFN2PFNMap
    t.LFN2transferItemMap = LFN2transferItemMap
    path = '/path/to/gfal.log'
    config.args = Namespace(gfal_log_path=path)
    with patch('ASO.Rucio.Actions.MonitorLockStatus.callGfalRm', autospec=True) as mock_callgfalRm:
        m = MonitorLockStatus(t, Mock(), Mock())
        m.cleanupTempArea(fileDocs)
        expectedPFNs = LFN2PFNMap['T2_CH_CERN_Temp'].values()
        mock_callgfalRm.side_effect = [True]*len(expectedPFNs)
        for pfn in expectedPFNs :
            assert call(pfn, path) in mock_callgfalRm.call_args_list



@pytest.mark.skip(reason="Laziness.")
def test_CleanUpTempArea_allFailed():
    assert 0 == 1

@pytest.mark.skip(reason="Laziness.")
def test_CleanUpTempArea_mixed():
    assert 0 == 1
