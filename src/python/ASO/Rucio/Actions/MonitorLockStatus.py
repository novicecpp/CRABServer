import logging

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
        okReplicas, notOKReplicas = self.checkLocksStatus()
        self.logger.debug(f'okReplicas: {okReplicas}')
        self.logger.debug(f'notOKReplicas: {notOKReplicas}')
        # update not ok replicas
        if notOKReplicas:
            notOKFileDoc = self.prepareNotOKFileDoc(notOKReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', notOKFileDoc, self.logger)
        # register okReplicas in publishContainer
        r = RegisterReplicas(self.transfer, self.rucioClient, None)
        newR = r.addReplicasToContainer(okReplicas, self.transfer.publishContainer)
        # Update dataset name for each replicas
        # may change data structure return from checklockstatus to dict later
        LFN2DatasetMap = {x['name']:x['dataset'] for x in newR}
        for i in okReplicas:
            i['dataset'] = LFN2DatasetMap[i['name']]
        self.logger.debug(f'okReplicas after add replicas to publishContainer: {okReplicas}')

        okFileDoc1 = self.prepareOKFileDoc(okReplicas)
        updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', okFileDoc1, self.logger)

        self.updateBlockCompleteStatus(okReplicas)
        self.logger.debug(f'okReplicas after update block completion: {okReplicas}')
        okFileDoc2 = self.prepareOKFileDoc(okReplicas)
        updateDB(self.crabRESTClient, 'filetransfers', 'updateRucioInfo', okFileDoc2, self.logger)
        self.transfer.updateTransferOKReplicas([x['name'] for x in okReplicas])

    def checkLocksStatus(self):
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

    def prepareOKFileDoc(self, replicas):
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
        return fileDoc

    def prepareNotOKFileDoc(self, replicas):
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
        return fileDoc
