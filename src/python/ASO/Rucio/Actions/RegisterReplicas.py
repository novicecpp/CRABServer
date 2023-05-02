import logging
import itertools
from ASO.Rucio.Actions.BuildTaskDataset import BuildTaskDataset
from rucio.rse.rsemanager import find_matching_scheme
from rucio.common.exception import FileAlreadyExists

from ASO.Rucio.exception import RucioTransferException
from ASO.Rucio.utils import chunks
import ASO.Rucio.config as config


class RegisterReplicas:
    def __init__(self, transfer, rucioClient, crabRestClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.RegisterReplicas")
        self.rucioClient = rucioClient
        self.transfer = transfer
        self.crabRestClient = crabRestClient

    def execute(self):
        start = self.transfer.lastTransferLine
        if config.config.force_total_files:
            end = config.config.force_total_files
        else:
            end = len(self.transfer.lastTransferLine)
        transferGenerator = itertools.islice(self.transfer.transferItems, start, end)
        preparedReplicasByRSE = self.prepare(transferGenerator)
        success, fail = self.register(preparedReplicasByRSE)
        return (success, fail)

    def prepare(self, transfers):
        # create bucket rse
        bucket = {}
        replicasByRSE = {}
        transfers = [x for x in transfers if not x['destination_lfs'] in self.transfer.replicasInRucio]
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
                if config.config.force_replica_name_suffix:
                    replicaName = f"{xdict['destination_lfn']}_{config.config.force_replica_name_suffix}"
                else:
                    replicaName = xdict['destination_lfn']
                replica = {
                    'scope': self.transfer.rucioScope,
                    'pfn': f'{pfnPrefix}{xdict["source_lfn"]}',
                    'name': replicaName,
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
        self.logger.debug(f'PrepareReplicas: {prepareReplicas}')
        # Ii will treat as fail the whole chunks if one of replicas is fail.
        b = BuildTaskDataset(self.transfer, self.rucioClient)
        for rse, replicas in prepareReplicas.items():
            for chunk in chunks(replicas, config.config.replicas_chunk_size):
                try:
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
                if num >= config.config.max_file_per_dataset:
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
