import logging
from ServerUtilities import encodeRequest

from ASO.Rucio.exception import RucioTransferException

class UpdateStatusToREST:
    def __init__(self, crabRESTClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.UpdateStatusToREST")
        self.crabRESTClient = crabRESTClient

    def execute(self):
        raise NotImplementedError

    def updateRegisteredTransfers(self, successReplicas, failReplicas):
        # success doc
        numSuccessReplicas = len(successReplicas)
        if numSuccessReplicas:
            successFileDoc = {
                'asoworker': 'rucio',
                'list_of_ids': [x['id'] for x in successReplicas],
                'list_of_transfer_state': ['SUBMITTED']*numSuccessReplicas,
                'list_of_dbs_blockname': [successReplicas[0]['dataset']]*numSuccessReplicas,
                'list_of_block_complete': ['NO']*numSuccessReplicas,
                'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/']*numSuccessReplicas,
                'list_of_failure_reason': None, # omit
                'list_of_retry_value': None, # omit
                'list_of_fts_id': ['NA']*numSuccessReplicas,
            }
            self.updateDB('updateTransfers', successFileDoc)
        # failed doc
        numFailReplicas = len(failReplicas)
        if numFailReplicas:
            failFileDoc = {
                'asoworker': 'rucio',
                'list_of_ids': [x['id'] for x in failReplicas],
                'list_of_transfer_state': ['FAILED']*numFailReplicas,
                'list_of_dbs_blockname': None,  # omit
                'list_of_block_complete': None, # omit
                'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/']*numFailReplicas,
                'list_of_failure_reason': ['Failed to register files within RUCIO']*numFailReplicas,
                # No need for retry -> delegate to RUCIO
                'list_of_retry_value': [0]*numFailReplicas,
                'list_of_fts_id': ['NA']*numFailReplicas,
            }
            self.updateDB('updateTransfers', failFileDoc)

    def updateDB(self, subresource, fileDoc):
        fileDoc['subresource'] = subresource
        self.crabRESTClient.post(
            api='filetransfers',
            data=encodeRequest(fileDoc)
        )
