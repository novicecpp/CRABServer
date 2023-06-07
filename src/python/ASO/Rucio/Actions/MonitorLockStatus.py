import logging
import copy

import ASO.Rucio.config as config
from ASO.Rucio.utils import updateDB
from ASO.Rucio.Actions.RegisterReplicas import RegisterReplicas

class MonitorLockStatus:
    def __init__(self, transfer, rucioClient, crabRESTClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.MonitorLocksStatus")
        self.rucioClient = rucioClient
        self.transfer = transfer
        self.crabRESTClient = crabRESTClient

    def execute(self):
        okReplicas, notOKReplicas = self.checkLockStatus()
        self.logger.debug(f'okReplicas: {okReplicas}')
        self.logger.debug(f'notOKReplicas: {notOKReplicas}')
        # update not-ok status
        self.updateNotOKReplicasToREST(notOKReplicas)

        # register to publish container
        self.registerToPublishContainer(okReplicas)
        self.logger.debug(f'okReplicas after add replicas to publishContainer: {okReplicas}')
        # update ok status
        self.updateOKReplicasToREST(okReplicas)

        # update block complete status
        self.updateBlockCompleteStatus(okReplicas)
        self.logger.debug(f'okReplicas after update block completion: {okReplicas}')

        # bookkeeping published replicas
        self.transfer.updateTransferOKReplicas([x['name'] for x in okReplicas])

    def checkLockStatus(self):
        okReplicas = []
        notOKReplicas = []
        try:
            listReplicasLocks = self.rucioClient.list_replica_locks(self.transfer.containerRuleID)
        except TypeError:
            # Current rucio-clients==1.29.10 will raise exception when it get
            # None response from server. It will happen when we run
            # list_replica_locks immediately after register replicas with
            # replicas lock info is not available yet.
            self.logger.info('TypeError has raised. Assume there is still no lock info available yet.')
            listReplicasLocks = []
        replicasInContainer = self.transfer.replicasInContainer[self.transfer.transferContainer]
        for replicaStatus in listReplicasLocks:
            # Skip replicas that register in the same run.
            if not replicaStatus['name'] in replicasInContainer:
                continue
            # skip if replicas transfer is in transferOKReplicas. No need to
            # update status for transfer complete.
            # Note that this will update `tm_block_complete` column to `OK`
            # for some, but not all, replicas in the block. Besure checking
            # block completion with `any` instead of `all` condition.
            if replicaStatus['name'] in self.transfer.transferOKReplicas:
                continue

            replica = {
                'id': self.transfer.replicaLFN2IDMap[replicaStatus['name']],
                'name': replicaStatus['name'],
                'dataset': None,
                'blockcomplete': 'NO',
                'ruleid': self.transfer.containerRuleID,
            }
            if replicaStatus['state'] == 'OK':
                okReplicas.append(replica)
            else:
                # TODO: if now - replica["created_at"] > 12h:
                # delete replica and detach from dataset --> treat as STUCK
                notOKReplicas.append(replica)
        return (okReplicas, notOKReplicas)

    def registerToPublishContainer(self, replicas):
        r = RegisterReplicas(self.transfer, self.rucioClient, None)
        replicasPublishedInfo = r.addReplicasToContainer(replicas, self.transfer.publishContainer)
        # Update dataset name for each replicas
        tmpLFN2DatasetMap = {x['name']:x['dataset'] for x in replicasPublishedInfo}
        for i in replicas:
            i['dataset'] = tmpLFN2DatasetMap[i['name']]

    def updateBlockCompleteStatus(self, replicas):
        """
        We can rely on `is_open` dataset metadata because we only add replicas with transfer complete to dataset in publish container
        """
        datasetsMap = {}
        for i in replicas:
            dataset = i['dataset']
            if not dataset in datasetsMap:
                datasetsMap[dataset] = [i]
            else:
                datasetsMap[dataset].append(i)
        for k, v in datasetsMap.items():
            metadata = self.rucioClient.get_metadata(self.transfer.rucioScope, k)
            if not metadata['is_open']:
                for r in v:
                    r['blockcomplete'] = 'OK'

    def updateOKReplicasToREST(self, replicas):
        """
        In case REST expected upload success and fail doc in time the reNot sure on the REST side if it support
        """
        num = len(replicas)
        fileDoc = {
            'asoworker': 'rucio',
            'list_of_ids': [x['id'] for x in replicas],
            'list_of_transfer_state': ['DONE']*num,
            'list_of_dbs_blockname': [x['dataset'] for x in replicas],
            'list_of_block_complete': [x['blockcomplete'] for x in replicas],
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/']*num,
            'list_of_failure_reason': None, # omit
            'list_of_retry_value': None, # omit
            'list_of_fts_id': ['NA']*num,
        }
        updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', fileDoc, self.logger)

    def updateBlockCompleteToREST(self, replicas):
        """

        """
        # TODO: This can be optimize to single REST API call
        num = len(replicas)
        fileDoc = {
            'asoworker': 'rucio',
            'list_of_ids': [x['id'] for x in replicas],
            'list_of_transfer_state': ['DONE']*num,
            'list_of_dbs_blockname': [x['dataset'] for x in replicas],
            'list_of_block_complete': [x['blockcomplete'] for x in replicas],
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/']*num,
            'list_of_failure_reason': None, # omit
            'list_of_retry_value': None, # omit
            'list_of_fts_id': ['NA']*num,
        }
        updateDB(self.crabRESTClient, 'filetransfers', 'updateRucioInfo', fileDoc, self.logger)


    def updateNotOKReplicasToREST(self, replicas):
        num = len(replicas)
        fileDoc = {
            'asoworker': 'rucio',
            'list_of_ids': [x['id'] for x in replicas],
            'list_of_transfer_state': ['SUBMITTED']*num,
            'list_of_dbs_blockname': None, # omit
            'list_of_block_complete': None, # omit
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/']*num,
            'list_of_failure_reason': None, # omit
            'list_of_retry_value': None, # omit
            'list_of_fts_id': [x['ruleid'] for x in replicas],
        }
        updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', fileDoc, self.logger)
