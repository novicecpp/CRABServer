import logging
import json
import os


from ASO.Rucio.exception import RucioTransferException
import ASO.Rucio.config as config

REST_INFO_PATH = 'task_process/RestInfoForFileTransfers.json'
TRANSFER_INFO_PATH = 'task_process/transfers.txt'

class Transfer:
    def __init__(self):
        self.logger = logging.getLogger('RucioTransfer.Transfer')

        # from rest info
        self.proxypath = ''

        # from transfer info
        self.username = ''
        self.rucioScope = ''
        self.destination = ''
        self.publishname = ''
        self.logsDataset = ''

        # dynamically change throughout the scripts
        self.currentDataset = ''

    def readInfo(self):
        try:
            with open(REST_INFO_PATH, 'r', encoding='utf-8') as r:
                restInfo = json.load(r)
                self.proxypath = restInfo['proxyfile']
        except FileNotFoundError as ex:
            raise RucioTransferException(f'{REST_INFO_PATH} does not exist. Probably no completed jobs in the task yet') from ex

        try:
            with open(TRANSFER_INFO_PATH, 'r', encoding='utf-8') as r:
                transferInfo = json.loads(r.readline()) # read from first line
                self.username = transferInfo['username']
                self.rucioScope = f'user.{transferInfo["username"]}'
                self.destination = transferInfo['destination']
                if config.config.force_publishname:
                    self.publishname = config.config.force_publishname
                else:
                    self.publishname = transferInfo['outputdataset']
                self.logsDataset = f'{self.publishname}#LOGS'
        except FileNotFoundError as ex:
            raise RucioTransferException(f'{REST_INFO_PATH} does not exist. Probably no completed jobs in the task yet') from ex
