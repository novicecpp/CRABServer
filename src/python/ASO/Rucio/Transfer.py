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
        self.restHost = ''
        self.restDBinstance = ''
        self.restProxyFile = ''


        # from transfer info
        self.username = ''
        self.rucioScope = ''
        self.destination = ''
        self.publishname = ''
        self.logsDataset = ''

        # dynamically change throughout the scripts
        self.currentDataset = ''

        # bookkeeping
        self.lastTransferLine = 0

        # rule bookkeeping
        self.allRules = None
        self.okRules = None

    def readInfo(self):
        """
        Read the information from input files using path from configuration.
        It needs to execute to following order because of dependency between method.
        """
        self.readLastTransferLine()
        self.readTransferItems()
        self.readRESTInfo()
        self.readInfoFromTransferItems()
        self.readBookkeepingRules()

    def readLastTransferLine(self):
        if config.config.force_last_line != None: #  Need explicit compare to None
            self.lastTransferLine = config.config.force_last_line
            return
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
                for line in r:
                    doc = json.loads(line)
                    self.transferItems.append(doc)
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
        if config.config.force_publishname:
            self.publishname = config.config.force_publishname
        else:
            self.publishname = info['outputdataset']
        self.logsDataset = f'{self.publishname}#LOGS'

    def readBookkeepingRules(self):
        path = config.config.bookkeeping_rules_path
        try:
            with open(path, 'r', encoding='utf-8') as r:
                doc = json.load(r)
                self.allRules = doc['all']
                self.okRules = doc['ok']
        except FileNotFoundError as ex:
            self.logger.info(f'Bookkeeping rules "{path}" does not exist. Assume it is first time it run.')
            self.allRules = []
            self.okRules = []

    def updateOKRules(self, rules):
        path = config.config.bookkeeping_rules_path
        if not all(x in self.allRules for x in rules):
            raise RucioTransferException('Some rules are not in "all" list')
        else:
            self.okRules += rules
        with somecontextlibfunc(path) as tmpPath:
            with open(tmpPath, 'w', encoding='utf-8') as w:
                doc = {
                    'all': self.allRules,
                    'ok': self.okRules
                }
                json.dump(doc, w)

    def addNewRule(self, rule):
        path = config.config.bookkeeping_rules_path
        self.allRules.append(rule)
        with somecontextlibfunc(path) as tmpPath:
            with open(tmpPath, 'w', encoding='utf-8') as w:
                doc = {
                    'all': self.allRules,
                    'ok': self.okRules,
                }
                json.dump(doc, w)






from contextlib import contextmanager
import shutil

@contextmanager
def somecontextlibfunc(path):
    tmpPath = f'{path}_tmp'
    yield tmpPath
    shutil.move(tmpPath, path)
