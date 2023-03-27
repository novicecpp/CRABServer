import logging

from ASO.Rucio.RunTransfer import RunTransfer

class RucioTransferMain:
    def __init__(self):
        self._initLogger()
        self.logger = logging.getLogger('RucioTransfer.RucioTransferMain')

    def run(self):
        print("executing RunTransfer")
        try:
            self.logger.info('executing RunTransfer')
            run = RunTransfer()
            run.algorithm()
        except Exception as ex:
            self.logger.exception("error during main loop %s", ex)
        self.logger.info('transfer completed')

    def _initLogger(self):
        logger = logging.getLogger('RucioTransfer')
        logger.setLevel(logging.DEBUG)
        hldr = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        hldr.setFormatter(formatter)
        logger.addHandler(hldr)


def main():
    rucioTransfer = RucioTransferMain()
    rucioTransfer.run()


if __name__ == "__main__":
    main()
