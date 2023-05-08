import logging
import itertools
import copy
from ASO.Rucio.Actions.BuildDBSDataset import BuildDBSDataset
from rucio.rse.rsemanager import find_matching_scheme
from rucio.common.exception import FileAlreadyExists

import ASO.Rucio.config as config
from ASO.Rucio.exception import RucioTransferException
from ASO.Rucio.utils import chunks, updateDB



class RegisterReplicas:
    def __init__(self, transfer, rucioClient, crabRESTClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.RegisterReplicas")
        self.rucioClient = rucioClient
        self.transfer = transfer
        self.crabRESTClient = crabRESTClient

    def execute(self):
        start = self.transfer.lastTransferLine
        if config.args.force_total_files:
            end = config.args.force_total_files
        else:
            end = len(self.transfer.lastTransferLine)
        transferGenerator = itertools.islice(self.transfer.transferItems, start, end)
        preparedReplicasByRSE = self.prepare(transferGenerator)

        # Remove registered replicas
        replicasToRegisterByRSE, registeredReplicas = self.removeRegisteredReplicas(preparedReplicasByRSE)
        self.logger.debug(f'replicasToRegisterByRSE: {replicasToRegisterByRSE}')
        self.logger.debug(f'registeredReplicas: {registeredReplicas}')
        successReplicasFromRegister, failReplicas = self.register(replicasToRegisterByRSE)
        self.logger.debug(f'successReplicasFromRegister: {successReplicasFromRegister}')
        self.logger.debug(f'failReplicas: {failReplicas}')
        successReplicas = successReplicasFromRegister + registeredReplicas
        self.logger.debug(f'successReplicas: {successReplicas}')
        if successReplicas:
            successFileDoc = self.prepareSuccessFileDoc(successReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateRucioInfo', successFileDoc, self.logger)
        if failReplicas:
            failFileDoc = self.prepareFailFileDoc(failReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', failFileDoc, self.logger)

    def prepare(self, transfers):
        # create bucket rse
        bucket = {}
        replicasByRSE = {}
        for xdict in transfers:
            # /store/temp are register as `<site>_Temp` in rucio
            rse = f'{xdict["source"]}_Temp'
            if not rse in bucket:
                bucket[rse] = []
            bucket[rse].append(xdict)
        for rse in bucket:
            xdict = bucket[rse][0]
            # Need to remove '_Temp' suffix from rse to get proper PFN.
            # FIXME: need ref for better explaination
            pfn = self.getSourcePFN(xdict["source_lfn"], rse.split('_Temp')[0], xdict["destination"])
            pfnPrefix = pfn.split(xdict["source_lfn"])[0]
            replicasByRSE[rse] = []
            for xdict in bucket[rse]:
                replica = {
                    'scope': self.transfer.rucioScope,
                    'pfn': f'{pfnPrefix}{xdict["source_lfn"]}',
                    'name': xdict['destination_lfn'],
                    'bytes': xdict['filesize'],
                    # FIXME: not sure why we need str.rjust here
                    'adler32': xdict['checksums']['adler32'].rjust(8, '0'),
                    'id': xdict['id']
                }
                replicasByRSE[rse].append(replica)
        return replicasByRSE

    def register(self, prepareReplicas):
        successReplicas = []
        failReplicas = []
        self.logger.debug(f'Prepare replicas: {prepareReplicas}')
        # Ii will treat as fail the whole chunks if one of replicas is fail.
        b = BuildDBSDataset(self.transfer, self.rucioClient)
        for rse, replicas in prepareReplicas.items():
            for chunk in chunks(replicas, config.args.replicas_chunk_size):
                try:
                    # remove 'id' from dict
                    r = []
                    for c in chunk:
                        d = c.copy()
                        d.pop('id')
                        r.append(d)
                    if not self.rucioClient.add_replicas(rse, r):
                        failItems = [{
                            'id': x['id'],
                            'dataset': '',
                        } for x in chunk]
                        failReplicas.append(failItems)
                except Exception as ex:
                    self.logger.info("files were already registered, going ahead.")
                    raise RucioTransferException('getting proper exception') from ex
                dids = [{
                    'scope': self.transfer.rucioScope,
                    'type': "FILE",
                    'name': x["name"]
                } for x in chunk]
                # no need to try catch for duplicate content.
                # not sure if restart process is enough for the case of connection error
                self.rucioClient.add_files_to_datasets([{
                        'scope': self.transfer.rucioScope,
                        'name': self.transfer.currentDataset,
                        'dids': dids
                    }],
                    ignore_duplicate=True)
                successItems = [{
                    'id': x['id'],
                    'dataset': self.transfer.currentDataset
                } for x in chunk]
                successReplicas.append(successItems)
                # TODO: close if update comes > 4h, or is it a Publisher task?
                # check the current number of files in the dataset
                num = len(list(self.rucioClient.list_content(self.transfer.rucioScope, self.transfer.currentDataset)))
                if num >= config.args.max_file_per_dataset:
                    # -if everything full create new one
                    self.rucioClient.close(self.transfer.rucioScope, self.transfer.currentDataset)
                    newDataset = b.generateDatasetName()
                    b.createDataset(newDataset)
                    self.transfer.currentDataset = newDataset
        return successReplicas, failReplicas

    def getSourcePFN(self, sourceLFN, sourceRSE, destinationRSE):
        try:
            _, srcScheme, _, _ = find_matching_scheme(
                {"protocols": self.rucioClient.get_protocols(destinationRSE)},
                {"protocols": self.rucioClient.get_protocols(sourceRSE)},
                "third_party_copy_read",
                "third_party_copy_write",
            )
            did = f'{self.transfer.rucioScope}:{sourceLFN}'
            sourcePFNMap = self.rucioClient.lfns2pfns(sourceRSE, [did], operation="third_party_copy_read", scheme=srcScheme)
            return sourcePFNMap[did]
        except Exception as ex:
            raise RucioTransferException("Failed to get source PFN") from ex


    def removeRegisteredReplicas(self, replicasByRSE):
        """
        It might better to get state from rest once at startup and just skip at
        prepare.
        """
        notRegister = copy.deepcopy(replicasByRSE)
        registered = []
        for k, v in notRegister.items():
            newV = []
            for i in range(len(v)):
                if v[i]['name'] in self.transfer.replicasInContainer:
                    registeredReplica = {
                        'id': v[i]['id'],
                        'dataset': self.transfer.replicasInContainer[v[i]['name']],
                    }
                    registered.append(registeredReplica)
                else:
                    newV.append(v[i])
            notRegister[k] = newV
        return notRegister, registered

    def prepareSuccessFileDoc(self, replicas):
        num = len(replicas)
        fileDoc = {
            'asoworker': 'rucio',
            'list_of_ids': [x['id'] for x in replicas],
            'list_of_transfer_state': ['SUBMITTED']*num,
            'list_of_dbs_blockname': [x['dataset'] for x in replicas],
            'list_of_block_complete': ['NO']*num,
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/']*num,
            'list_of_failure_reason': None, # omit
            'list_of_retry_value': None, # omit
            'list_of_fts_id': ['NA']*num,
        }
        return fileDoc

    def prepareFailFileDoc(self, replicas):
        num = len(replicas)
        fileDoc = {
            'asoworker': 'rucio',
            'list_of_ids': [x['id'] for x in replicas],
            'list_of_transfer_state': ['FAILED']*num,
            'list_of_dbs_blockname': None,  # omit
            'list_of_block_complete': None, # omit
            'list_of_fts_instance': ['https://fts3-cms.cern.ch:8446/']*num,
            'list_of_failure_reason': ['Failed to register files within RUCIO']*num,
            'list_of_retry_value': [0]*num, # No need for retry -> delegate to RUCIO
            'list_of_fts_id': ['NA']*num,
        }
        return fileDoc
