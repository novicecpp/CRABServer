import logging

class MonitorLocksStatus:
    def __init__(self, transfer, rucioClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.BuildTaskDataset")
        self.rucioClient = rucioClient
        self.transfer = transfer

    def execute(self):
        # only process non-ok rule from bookkeeping
        ruleToMontior = [x for x in self.transfer.allRules if not x in self.transfer.okRules]
        retOKReplicas, retNotOKReplicas, retOKRuleIDs = self.checkLocksStatus(ruleToMontior)
        self.transfer.updateOKRules(retOKRuleIDs)

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
