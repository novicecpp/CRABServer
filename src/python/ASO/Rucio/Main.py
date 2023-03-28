""" docs
"""

import logging

from argparse import ArgumentParser

from ASO.Rucio.RunTransfer import RunTransfer

class RucioTransferMain:
    def __init__(self, opts):
        self._initLogger()
        self.logger = logging.getLogger('RucioTransfer.RucioTransferMain')

    def run(self):
        print("executing RunTransfer")
        try:
            self.logger.info('executing RunTransfer')
            run = RunTransfer()
            run.algorithm()
        except Exception as ex:
            self.logger.exception("unexpected error during main loop %s", ex)
            raise ex
        self.logger.info('transfer completed')

    def _initLogger(self):
        logger = logging.getLogger('RucioTransfer')
        logger.setLevel(logging.DEBUG)
        hldr = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        hldr.setFormatter(formatter)
        logger.addHandler(hldr)


def main():
    opt = ArgumentParser(usage=__doc__)
    opt.add_argument("--force-dataset-name", dest="force_dataset_name", default=None,
                     help="use provided output dataset name instead of output")
    opts = opt.parse_args()

    rucioTransfer = RucioTransferMain(opts)

    rucioTransfer.run()


if __name__ == "__main__":
    main()
