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

from unittest.mock import patch, Mock, call
import pytest
import datetime

from ASO.Rucio.Actions.MonitorLocksStatus import MonitorLocksStatus

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
    getReplicationRuleReturnValue = {
        'id': 'b43a554244c54dba954aa29cb2fdde0a',
        'name': '/GenericTTbar/tseethon-autotest-1679671056-94ba0e06145abd65ccb1d21786dc7e1d/USER#c9b28b96-5d16-41cd-89af-2678971132c9',
        'state': 'OK',
    }
    listReplicaLocksReturnValue = [{
        'name': '/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root',
        'state': 'OK',
    }]
    mock_rucioClient.get_replication_rule.return_value = getReplicationRuleReturnValue
    mock_rucioClient.list_replica_locks.side_effect = ((x for x in listReplicaLocksReturnValue), ) # list_replica_locks return generator
    mock_Transfer.getIDFromLFN.return_value = '98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca'
    m = MonitorLocksStatus(mock_Transfer, mock_rucioClient, Mock())
    assert m.checkLocksStatus(listRuleIDs) == (outputAllOK, [], ["b43a554244c54dba954aa29cb2fdde0a"])

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
