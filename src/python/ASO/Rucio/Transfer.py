import logging
import json
import os


from ASO.Rucio.exception import RucioTransferException
import ASO.Rucio.config as config

class Transfer:
    """
    Use Transfer object to store state of process in memory.
    It responsible for read info from file and set its attribute.
    This object will pass to Actions class as mutable input.
    """
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
        """
        Read the information from input files using path from configuration.
        It needs to execute to following order because of dependency between method.
        """
        self.readLastTransferLine()
        self.readTransferItems()
        self.readRESTInfo()
        self.readInfoFromTransferItems()

    def readLastTransferLine(self):
        path = config.config.last_line_path
        try:
            with open(path, 'r', encoding='utf-8') as r:
                self.lastTransferLine = int(r.read())
        except FileNotFoundError:
            self.logger.info(f'{path} not found. Assume it is first time it run.')
            self.lastTransferLine = 0

    def readTransferItems(self):
        path = config.config.transfers_txt_path
        self.transferItems = []
        try:
            with open(path, 'r', encoding='utf-8') as r:
                for _ in range(self.lastTransferLine):
                    r.readline()
                for line in r:
                    doc = json.loads(line)
                    self.transferItems.append(doc)
                    self.lastTransferLine += 1
        except FileNotFoundError as ex:
            raise RucioTransferException(f'{path} does not exist. Probably no completed jobs in the task yet.') from ex
        if len(self.transferItems) == 0:
            raise RucioTransferException(f'{path} does not contain new entry.')

    def readRESTInfo(self):
        path = config.config.rest_info_path
        try:
            with open(path, 'r', encoding='utf-8') as r:
                doc = json.loads(r.read())
                self.restHost = doc['host']
                self.restDBinstance = doc['dbInstance']
                self.restProxyFile = doc['proxyfile']
        except FileNotFoundError as ex:
            raise RucioTransferException(f'{path} does not exist. Probably no completed jobs in the task yet.') from ex

    def readInfoFromTransferItems(self):
        info = self.transferItems[0]
        self.username = info['username']
        self.rucioScope = f'user.{self.username}'
        self.destination = info['destination']
        self.publishname = info['publishname']
        self.logsDataset = f'{self.publishname}#LOGS'
