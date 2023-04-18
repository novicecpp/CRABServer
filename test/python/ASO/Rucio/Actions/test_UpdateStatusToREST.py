# old code
# caller
# ====================================
# to_update_success_docs = make_filedoc_for_db(
#     ids=[glob.id2lfn_map[x['lfn']] for x in success_from_registration],
#     states=["SUBMITTED" for x in success_from_registration],
#     dbsBlocknames=[x['dbsBlock'] for x in success_from_registration],
#     blockCompletes=[x['complete'] for x in success_from_registration],
#     reasons=None
# )
# ===================
# new code value return from RegisterReplicas
# =====================
#    expectedSuccess = [
#        {
#            "name": "/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root",
#            "dataset": mock_Transfer.currentDataset,
#        }
#    ]
# ===================
#  and this is value make_filedoc_for_db needs
# ==================
#    fileDoc['asoworker'] = 'rucio'
#    fileDoc['subresource'] = 'updateTransfers'
#    fileDoc['list_of_ids'] = ids
#    fileDoc['list_of_transfer_state'] = states
#    fileDoc['list_of_dbs_blockname'] = dbsBlocknames
#    fileDoc['list_of_block_complete'] = blockCompletes
#    fileDoc['list_of_fts_instance'] = [
#        'https://fts3-cms.cern.ch:8446/' for _ in ids]
#    if reasons:
#        if len(reasons) != len(ids):
#            raise
#        fileDoc['list_of_failure_reason'] = reasons
#        # No need for retry -> delegate to RUCIO
#        fileDoc['list_of_retry_value'] = [0 for _ in ids]
#    if rule_ids:
#        fileDoc['list_of_fts_id'] = [x for x in rule_ids]
#    else:
#        fileDoc['list_of_fts_id'] = ['NA' for _ in ids]

import pytest
import json
from unittest.mock import patch, Mock

from ASO.Rucio.Actions.UpdateStatusToREST import UpdateStatusToREST

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
def mock_crabserver():
    with patch('RESTInteractions.CRABRest', autospec=True) as client:
        return client

def generateExpectedOutput(doctype, dataset):
    if doctype == 'success':
        return {
            'asoworker': 'rucio',
            'list_of_ids': ['some_id_from_transfer.txt'], # hmm, how do we get this
            'list_of_transfer_state': ['SUBMITTED'],
            'list_of_dbs_blockname': [dataset],
            'list_of_block_complete': ['NO'],
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/'],
            'list_of_failure_reason': None, # omit
            'list_of_retry_value': None, # omit
            'list_of_fts_id': ['NA'],
        }
    elif doctype == 'fail':
        return {
            'asoworker': 'rucio',
            'list_of_ids': ['some_id_from_transfer.txt'], # hmm, how do we get this
            'list_of_transfer_state': ['FAILED'],
            'list_of_dbs_blockname': None,  # omit
            'list_of_block_complete': None, # omit
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/'],
            'list_of_failure_reason': ['Failed to register files within RUCIO'],
            # No need for retry -> delegate to RUCIO
            'list_of_retry_value': [0],
            'list_of_fts_id': ['NA'],
        }


def test_makefileDoc_success_register_replica(mock_crabserver, mock_Transfer):
    registerReplicasOutput = [
        {
            "id": "98f353b91ec84f0217da80bde84d6b520c0c6640f60ad9aabb7b20ca",
            "dataset": mock_Transfer.currentDataset,
        }
    ]
    expectedOutput = generateExpectedOutput('success', mock_Transfer.currentDataset)
    u = UpdateStatusToREST(mock_crabserver)
    assert u.makeFileDoc(registerReplicasOutput) == expectedOutput

def test_makefileDoc_fail_register_replica(mock_crabserver, mock_Transfer):
    registerReplicasOutput = [
        {
            "name": "/store/user/rucio/tseethon/test-workflow/GenericTTbar/autotest-1679671056/230324_151740/0000/output_9.root",
            "dataset": mock_Transfer.currentDataset,
        }
    ]
    expectedOutput = generateExpectedOutput('fail', mock_Transfer.currentDataset)
    u = UpdateStatusToREST(mock_crabserver)
    assert u.makeFileDoc(registerReplicasOutput) == expectedOutput

def test_updateDB_of_register_replica(mock_crabserver):
    u = UpdateStatusToREST(mock_crabserver)
    expectedOutput = generateExpectedOutput('success', mock_Transfer.currentDataset)
    subresource = 'updateTransfers'
    u.updateDB(subresource, expectedOutput)
    mock_crabserver.post.assert_called_once_with(subresource, expectedOutput)
