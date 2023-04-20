import logging

from ASO.Rucio.utils import updateDB

class MonitorLocksStatus:
    def __init__(self, transfer, rucioClient, crabRESTClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.BuildTaskDataset")
        self.rucioClient = rucioClient
        self.transfer = transfer
        self.crabRESTClient = crabRESTClient

    def execute(self):
        # only process non-ok rule from bookkeeping
        ruleToMontior = [x for x in self.transfer.allRules if not x in self.transfer.okRules]
        retOKReplicas, retNotOKReplicas, retOKRules = self.checkLocksStatus(ruleToMontior)
        if retOKReplicas:
            OKFileDoc = self.prepareOKFileDoc(retOKReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateRucioInfo', OKFileDoc, self.logger)
        if retNotOKReplicas:
            NotOKFileDoc = self.prepareNotOKFileDoc(retNotOKReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', NotOKFileDoc, self.logger)
        self.transfer.updateOKRules(retOKRules)

    def checkLocksStatus(self, ruleIDs):
        OKReplicas = []
        OKRuleIDs = []
        notOKReplicas = []
        for rule in ruleIDs:
            ruleStatus = self.rucioClient.get_replication_rule(rule)
            # FIXME: sometime we got error that rucioClient cannot parse response of
            # list_replica_locks and raise TypeError.
            # Not sure how to handle this
            if ruleStatus['state'] == 'OK':
                blockComplete = 'OK'
                OKRuleIDs.append(rule)
            else:
                blockComplete = 'NO'
            for replicaStatus in self.rucioClient.list_replica_locks(rule):
                replica = {
                    "id": self.transfer.getIDFromLFN(replicaStatus['name']),
                    "dataset": ruleStatus['name'],
                    "blockcomplete": blockComplete,
                    "ruleid": rule,
                }
                if replicaStatus['state'] == 'OK':
                    OKReplicas.append(replica)
                else:
                    # TODO:   if now - replica["created_at"] > 12h:
                    # delete replica and detach from dataset --> treat as STUCK
                    notOKReplicas.append(replica)
        return (OKReplicas, notOKReplicas, OKRuleIDs)

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
