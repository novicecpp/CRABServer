import logging

import ASO.Rucio.config as config
from ASO.Rucio.utils import updateDB

class MonitorLocksStatus:
    def __init__(self, transfer, rucioClient, crabRESTClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.MonitorLocksStatus")
        self.rucioClient = rucioClient
        self.transfer = transfer
        self.crabRESTClient = crabRESTClient

    def execute(self):
        okReplicas, notOKReplicas = self.checkLocksStatus()
        self.logger.debug(f'okReplicas: {okReplicas}')
        self.logger.debug(f'notOKReplicas: {notOKReplicas}')
        if okReplicas:
            okFileDoc = self.prepareOKFileDoc(okReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', okFileDoc, self.logger)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateRucioInfo', okFileDoc, self.logger)
        if notOKReplicas:
            notOKFileDoc = self.prepareNotOKFileDoc(notOKReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', notOKFileDoc, self.logger)

    def checkLocksStatus(self):
        okReplicas = []
        notOKReplicas = []
        replicasByDataset = {}
        try:
            listReplicasLocks = self.rucioClient.list_replica_locks(self.transfer.containerRuleID)
        except TypeError:
            # Current rucio-clients==1.29.10 will raise exception when it get
            # None response from server. It will happen when we run
            # list_replica_locks immediately after register replicas with
            # replicas lock info is not available yet.
            self.logger.info('TypeError has raised. Assume there is still no lock info available yet.')
            listReplicasLocks = []
        for replicaStatus in listReplicasLocks:
            # Skip replicas that registered in the same run.
            if not replicaStatus['name'] in self.transfer.replicasInContainer:
                continue
            blockName = self.transfer.replicasInContainer[replicaStatus['name']]
            replica = {
                'id': self.transfer.replicaLFN2IDMap[replicaStatus['name']],
                'dataset': blockName,
                'blockcomplete': 'NO',
                'ruleid': self.transfer.containerRuleID,
                'state': replicaStatus['state'],
            }
            # Block complete state rely on `config.args.max_file_per_dataset`.
            # Beware blockcomplete will alway "NO" if we rerun script while
            # change max_file_per_dataset to bigger value when register
            # replicas.
            if not blockName in replicasByDataset:
                replicasByDataset[blockName] = []
            replicasByDataset[blockName].append(replica)
        self.logger.debug(f'replicaByDataset dict: {replicasByDataset}')
        for k, v in replicasByDataset.items():
            if len(v) >= config.args.max_file_per_dataset \
               and all(x['state'] == 'OK' for x in v):
                self.logger.debug(f'Dataset "{k}" is all OK.')
                blockComplete = 'OK'
            else:
                self.logger.debug(f'Dataset "{k}" is still replicating.')
                blockComplete = 'NO'
            for replica in v:
                # change blockcomplete to OK when all block
                replica['blockcomplete'] = blockComplete
                # remove unnecessary key
                state = replica.pop('state')
                if state == 'OK':
                    okReplicas.append(replica)
                else:
                    # TODO: if now - replica["created_at"] > 12h:
                    # delete replica and detach from dataset --> treat as STUCK
                    notOKReplicas.append(replica)
        return (okReplicas, notOKReplicas)

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
