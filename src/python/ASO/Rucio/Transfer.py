import logging
import json
import os


from ASO.Rucio.exception import RucioTransferException

REST_INFO_PATH = 'task_process/RestInfoForFileTransfers.json'
TRANSFER_INFO_PATH = 'task_process/transfers.txt'

class Transfer:
    def __init__(self):
        self.logger = logging.getLogger('RucioTransfer.Transfer')

        self.proxypath = None
        self._readRestInfo()

        self.username = None
        self.destination = None
        self.publishname = None
        self._readTransferInfo()

    def _readRestInfo(self):
        try:
            with open(REST_INFO_PATH, 'r', encoding='utf-8') as r:
                restInfo = json.load(r)
                self.proxypath = os.getcwd() + "/" + restInfo['proxyfile']
        except FileNotFoundError as ex:
            self.logger.error(f'{REST_INFO_PATH} does not exist. Probably no completed jobs in the task yet')
            raise ex

    def _readTransferInfo(self):
        try:
            with open(TRANSFER_INFO_PATH, 'r', encoding='utf-8') as r:
                transferInfo = json.loads(r.readline())
                self.user = transferInfo['username']
                self.destination = transferInfo['destiation']
                self.publishname = transferInfo['outputdataset']
        except FileNotFoundError as ex:
            self.logger.error(f'{TRANSFER_INFO_PATH} does not exist. Probably no completed jobs in the task yet')
            raise ex
