import logging
import itertools
import copy
from ASO.Rucio.Actions.BuildDBSDataset import BuildDBSDataset
from rucio.rse.rsemanager import find_matching_scheme
from rucio.common.exception import FileAlreadyExists

import ASO.Rucio.config as config
from ASO.Rucio.exception import RucioTransferException
from ASO.Rucio.utils import chunks, updateDB, tfcLFN2PFN, LFNToPFNFromPFN



class RegisterReplicas:
    """
    RegisterReplicas action is responsible for register new files in temp area to Rucio,
    close the current dataset and create new one when number of files is exceed `max_file_per_dataset`
    The transfering stuff is done by Rucio side (by the rule we created in BuildDBSDataset).
    """
    def __init__(self, transfer, rucioClient, crabRESTClient):
        self.logger = logging.getLogger("RucioTransfer.Actions.RegisterReplicas")
        self.rucioClient = rucioClient
        self.transfer = transfer
        self.crabRESTClient = crabRESTClient

    def execute(self):
        """
        Register replicas to dataset. Read list of files to transfer from
        self.transfer.transferItems, filter out, replicas that already registered in container.
        then register the new one. and attach it to datasets.
        """
        # Generate generator for range of transferItems we want to register.
        # This make it easier for do testing.
        start = self.transfer.lastTransferLine
        if config.args.force_total_files:
            end = start + config.args.force_total_files
        else:
            end = len(self.transfer.transferItems)
        transferGenerator = itertools.islice(self.transfer.transferItems, start, end)
        # Prepare
        preparedReplicasByRSE = self.prepare(transferGenerator)
        # Remove registered replicas
        replicasToRegisterByRSE, registeredReplicas = self.removeRegisteredReplicas(preparedReplicasByRSE)
        self.logger.debug(f'replicasToRegisterByRSE: {replicasToRegisterByRSE}')
        self.logger.debug(f'registeredReplicas: {registeredReplicas}')
        # Register only new transferItems
        successReplicasFromRegister, failReplicas = self.register(replicasToRegisterByRSE)
        self.logger.debug(f'successReplicasFromRegister: {successReplicasFromRegister}')
        self.logger.debug(f'failReplicas: {failReplicas}')
        # Merge already registered replicas and newly registered replicas
        successReplicas = successReplicasFromRegister + registeredReplicas
        self.logger.debug(f'successReplicas: {successReplicas}')
        # Create new entry in REST in FILETRANSFERDB table
        if successReplicas:
            successFileDoc = self.prepareSuccessFileDoc(successReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateRucioInfo', successFileDoc, self.logger)
        if failReplicas:
            failFileDoc = self.prepareFailFileDoc(failReplicas)
            updateDB(self.crabRESTClient, 'filetransfers', 'updateTransfers', failFileDoc, self.logger)
        # After everything is done, bookkeeping LastTransferLine.
        self.transfer.updateLastTransferLine(end)

    def prepare(self, transfers):
        """
        Convert from transferItems to ready-to-use variable for `register()` method.
        Receive generator of transferItems and construct replicas dictionary to register in Rucio.
        Replicas will group by source sites and return it as key-value of site and list of dicts that contain infomation needed for rucioClient.add_replicas function.

        The important thing is we still need resolve PFN manually because Temp RSE is declare as Non-deterministic.
        We rely on `ruciClient.lfn2pfns()` to determine PFN by passing normal RSE to this function and use it for Temp RSSE.

        :param transfers: the Generator which return each items in the

        :returns: dict map of `<site>_Temp` and list of dicts that replicas information.
        """
        # create bucket RSE
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
            # We determine PFN of Temp RSE from normal RSE.
            # Simply remove temp suffix before passing to getSourcePFN function.
            pfn = self.getSourcePFN(xdict["source_lfn"], rse.split('_Temp')[0], xdict["destination"])
            replicasByRSE[rse] = []
            for xdict in bucket[rse]:
                replica = {
                    'scope': self.transfer.rucioScope,
                    'pfn': LFNToPFNFromPFN(xdict["source_lfn"], pfn),
                    'name': xdict['destination_lfn'],
                    'bytes': xdict['filesize'],
                    'adler32': xdict['checksums']['adler32'].rjust(8, '0'),
                    # TODO: move id out of replicas info
                    'id': xdict['id'],
                }
                replicasByRSE[rse].append(replica)
        return replicasByRSE

    def register(self, prepareReplicas):
        """
        Register replicas to dataset via `rucioClient.add_replicas()` in chunks (chunk size is defined in `config.args.replicas_chunk_size`) and attach it to current dataset.
        Also, creating a new dataset when dataset has exceed `config.arg.max_file_per_datset`.

        :param prepareReplicas: dict of `<site>_Temp` and list of dicts that replicas information return from `prepare()` method.

        :returns: tuple of success and fail replicas which contain dict of infomation to create new entries in FILETRANSFERDB table in REST.
        """
        successReplicas = []
        failReplicas = []
        self.logger.debug(f'Prepare replicas: {prepareReplicas}')
        b = BuildDBSDataset(self.transfer, self.rucioClient)
        for rse, replicas in prepareReplicas.items():
            self.logger.debug(f'Registering replicas from {rse}')
            self.logger.debug(f'Replicas: {replicas}')
            for chunk in chunks(replicas, config.args.replicas_chunk_size):
                try:
                    # TODO: remove id from dict we construct in prepare() method.
                    # remove 'id' from dict
                    r = []
                    for c in chunk:
                        d = c.copy()
                        d.pop('id')
                        r.append(d)
                    # add_replicas with same dids will always return True, even
                    # with changing metadata (e.g pfn), rucio will not update to
                    # the new value.
                    # See https://github.com/dmwm/CMSRucio/issues/343#issuecomment-1543663323
                    retAddReplicas = self.rucioClient.add_replicas(rse, r)
                    if not retAddReplicas:
                        failItems = [{
                            'id': x['id'],
                            'dataset': '',
                        } for x in chunk]
                        failReplicas += failItems
                        continue
                except Exception as ex:
                    # Note that 2 exceptions we encounter so far here is due to
                    # LFN to PFN converstion and RSE protocols.
                    # https://github.com/dmwm/CRABServer/issues/7632
                    raise RucioTransferException('Something wrong with adding new replicas') from ex

                dids = [{
                    'scope': self.transfer.rucioScope,
                    'type': "FILE",
                    'name': x["name"]
                } for x in chunk]
                # no need to try catch for duplicate content. Not sure if
                # restart process is enough for the case of connection error
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
                successReplicas += successItems
                # Current algo will add files whole chunk, so total number of
                # files in dataset is at most is max_file_per_datset+replicas_chunk_size.
                #
                # check the current number of files in the dataset
                num = len(list(self.rucioClient.list_content(self.transfer.rucioScope, self.transfer.currentDataset)))
                if num >= config.args.max_file_per_dataset:
                    # FIXME: close the last dataset when ALL Postjob has reach timeout.
                    #        But, do we really need to close dataset?
                    self.rucioClient.close(self.transfer.rucioScope, self.transfer.currentDataset)
                    newDataset = b.generateDatasetName()
                    b.createDataset(newDataset)
                    self.transfer.currentDataset = newDataset
        return successReplicas, failReplicas

    def getSourcePFN(self, sourceLFN, sourceRSE, destinationRSE):
        """
        Get source PFN from `rucioClient.lfns2pfns()`.

        :param sourceLFN: source LFN
        :param sourceRSE: source RSE where LFN is reside, but it must be normal RSE name (e.g. `T2_CH_CERN` without suffix `_Temp`. Otherwise, it will raise exception in `lfns2pfns()`.
        :param destinationRSE: need it for select proper protocol for transfer with find_machine_scheme()

        :returns: string of PFN resolve from lfns2pfns
        """
        self.logger.debug(f'Getting pfn for {sourceLFN} at {sourceRSE}')
        try:
            _, srcScheme, _, _ = find_matching_scheme(
                {"protocols": self.rucioClient.get_protocols(destinationRSE)},
                {"protocols": self.rucioClient.get_protocols(sourceRSE)},
                "third_party_copy_read",
                "third_party_copy_write",
            )
            did = f'{self.transfer.rucioScope}:{sourceLFN}'
            sourcePFNMap = self.rucioClient.lfns2pfns(sourceRSE, [did], operation="third_party_copy_read", scheme=srcScheme)
            pfn = sourcePFNMap[did]
            self.logger.debug(f'PFN: {pfn}')
            return pfn
        except Exception as ex:
            raise RucioTransferException("Failed to get source PFN") from ex

    def getSourcePFN2(self, sourceLFN, sourceRSE):
        """
        Just for crosschecking with FTS algo we use in `getSourcePFN()`
        Will remove it later.
        """
        self.logger.debug(f'Getting pfn for {sourceLFN} at {sourceRSE}')
        rgx = self.rucioClient.get_protocols(
            sourceRSE, protocol_domain='ALL', operation="read")[0]
        didStr = f'{self.transfer.rucioScope}:{sourceLFN}'
        if not rgx['extended_attributes'] or 'tfc' not in rgx['extended_attributes']:
            pfn = self.rucioClient.lfns2pfns(
                sourceRSE, [didStr], operation="read")[didStr]
        else:
            tfc = rgx['extended_attributes']['tfc']
            tfc_proto = rgx['extended_attributes']['tfc_proto']
            pfn = tfcLFN2PFN(sourceLFN, tfc, tfc_proto)

        if sourceRSE == 'T2_DE_DESY':
            pfn = pfn.replace('/pnfs/desy.de/cms/tier2/temp', '/pnfs/desy.de/cms/tier2/store/temp')
        self.logger.debug(f'PFN2: {pfn}')
        return pfn

    def removeRegisteredReplicas(self, replicasByRSE):
        """
        Separate registered from unregister replicas. List of registered replicas are stored in `self.transfer.replicasInContainer`.

        :returns: tuple of
            - list of unregister replicas.
            - list of registered replicas in the same information returned by successReplicas from `register()` method.
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
        """
        This method is for successful registered replicas.

        Convert replicas info to fileDoc for store replicas infomation in REST.

        :param replicas: list of dict contain transferItems's ID and its information.

        :return: dict which use in `filetransfers` REST API.
        """
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
        """
        This method is for fail registered replicas.

        convert replicas info to fileDoc for store replicas infomation in REST.

        :param replicas: list of dict contain transferItems's ID and its information.

        :return: dict which use in `filetransfers` REST API.
        """
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
