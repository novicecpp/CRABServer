import logging

from ASO.Rucio.RunTransfer import RunTransfer
from python.ASO.Rucio.exception import RucioTransferException

class RucioTransferMain:
    def __init__(self):
        self._initLogger()
        self.logger = logging.getLogger('RucioTransfer.RucioTransferMain')

    def run(self):
        print("executing RunTransfer")
        run = RunTransfer()
        exception:

    def _initLogger():
        logger = logging.getLogger('RucioTransfer')
        logger.setLevel(logging.DEBUG)
        hldr = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        hldr.setFormatter(formatter)
        logger.addHandler(hldr)


except Exception as ex:



def main():
    rucioTransfer = RucioTransferMain()
    rucioTransfer.run()