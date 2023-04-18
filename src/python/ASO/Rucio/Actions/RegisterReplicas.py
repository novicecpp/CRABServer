import logging
from rucio.rse.rsemanager import find_matching_scheme

from ASO.Rucio.exception import RucioTransferException


class RegisterReplicas:
    def __init__(self, transfer, rucioClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.RegisterReplicas")
        self.rucioClient = rucioClient
        self.transfer = transfer
    def execute(self):
        raise NotImplementedError
    def register(self, prepareList):
        raise NotImplementedError
    def prepare(self, transferList):
        # create bucket rse
        bucket = {}
        replicasByRSE = {}
        for xdict in transferList:
            # /store/temp are register as `<site>_Temp` in rucio
            rse = f'{xdict["source"]}_Temp'
            if not rse in bucket:
                bucket[rse] = []
            bucket[rse].append(xdict)
        for rse in bucket:
            xdict = bucket[rse][0]
            pfn = self.getSourcePFN(xdict["source_lfn"], rse, xdict["destination"])
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
                }
                replicasByRSE[rse].append(replica)
        return replicasByRSE


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
