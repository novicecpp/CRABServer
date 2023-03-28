import logging
import json
import os


from ASO.Rucio.exception import RucioTransferException

REST_INFO_PATH = 'task_process/RestInfoForFileTransfers.json'
TRANSFER_INFO_PATH = 'task_process/transfers.txt'

class Transfer:
    def __init__(self):
        self.logger = logging.getLogger('RucioTransfer.Transfer')

        self.proxypath = ''
        self._readRestInfo()

        self.username = ''
        self.rucioScope = ''
        self.destination = ''
        self.publishname = ''
        self.logsDataset = ''
        self._readTransferInfo()

        # dynamically change throughout the scripts
        self.currentDataset = ''

    def _readRestInfo(self):
        try:
            with open(REST_INFO_PATH, 'r', encoding='utf-8') as r:
                restInfo = json.load(r)
                self.proxypath = os.getcwd() + "/" + restInfo['proxyfile']
        except FileNotFoundError as ex:
            raise RucioTransferException(f'{REST_INFO_PATH} does not exist. Probably no completed jobs in the task yet') from ex

    def _readTransferInfo(self):
        try:
            with open(TRANSFER_INFO_PATH, 'r', encoding='utf-8') as r:
                transferInfo = json.loads(r.readline()) # read from first line
                self.username = transferInfo['username']
                self.rucioScope = f'user.{transferInfo["username"]}'
                self.destination = transferInfo['destiation']
                self.publishname = transferInfo['outputdataset']
                self.logsDataset = f'{transferInfo["outputdataset"]}+#LOGS'
        except FileNotFoundError as ex:
            raise RucioTransferException(f'{REST_INFO_PATH} does not exist. Probably no completed jobs in the task yet') from ex
