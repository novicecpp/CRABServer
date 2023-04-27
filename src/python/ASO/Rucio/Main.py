import logging

from argparse import ArgumentParser

import ASO.Rucio.config as config
from ASO.Rucio.RunTransfer import RunTransfer
from ASO.Rucio.exception import RucioTransferException


class RucioTransferMain:
    """
    This class is entrypoint of RUCIO_Transfers.py It setup logs
    handlers and called RunTransfer to execute RUCIO_Transfers.py
    algorithm.
    """
    def __init__(self):
        self._initLogger()
        self.logger = logging.getLogger('RucioTransfer.RucioTransferMain')

    def run(self):
        """
        Execute RunTransfer.algorithm.
        Exception handling here is for debugging purpose. If
        RucioTransferException was raise, it mean some condition is
        not meet and we want to fail (fast) this process.  But if
        Exception is raise mean something gone wrong with our code and
        need to investigate.
        """
        self.logger.info("executing RunTransfer")
        try:
            self.logger.info('executing RunTransfer')
            run = RunTransfer()
            run.algorithm()
        except RucioTransferException as ex:
            raise ex
        except Exception as ex:
            raise Exception("Unexpected error during main") from ex
        self.logger.info('transfer completed')

    def _initLogger(self):
        logger = logging.getLogger('RucioTransfer')
        logger.setLevel(logging.DEBUG)
        hldr = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        hldr.setFormatter(formatter)
        logger.addHandler(hldr)


def main():
    """
    This main function is mean to called by RUCIO_Transfers.py script.
    Arguments are process here and only for run integration test or
    run process directly from this file.
    """
    opt = ArgumentParser(usage=__doc__)
    opt.add_argument("--force-publishname", dest="force_publishname", default=None, type=str,
                     help="use provided output dataset name instead of output")
    opt.add_argument("--force-last-line", dest="force_last_line", default=None, type=int,
                     help="")
    opt.add_argument("--force-total-files", dest="force_total_files", default=None, type=int,
                     help="")
    opt.add_argument("--force-replica-name-suffix", dest="force_replica_name_suffix", default=None, type=str,
                     help="")
    # default here must change because theses current value is too low (chunk=2/max=5)
    opt.add_argument("--replicas-chunk-size", dest="replicas_chunk_size", default=2, type=int,
                     help="")
    opt.add_argument("--max-file-per-dataset", dest="max_file_per_dataset", default=5, type=int,
                     help="")
    opt.add_argument("--last-line-path", dest="last_line_path",
                     default='task_process/transfers/last_transfer.txt',
                     help="")
    opt.add_argument("--transfer-txt-path", dest="transfers_txt_path",
                     default='task_process/transfers.txt',
                     help="")
    opt.add_argument("--rest-info-path", dest="rest_info_path",
                     default='task_process/RestInfoForFileTransfers.json',
                     help="")
    opt.add_argument("--bookkeeping-rules-path", dest="bookkeeping_rules_path",
                     default='task_process/transfers/bookkeeping_rules.json',
                     help="")
    opts = opt.parse_args()

    # Wa: I personally does not know how to mock this in unittest. I manually
    # instantiate new one in test function before run one.
    # Will switch to WMCore.Configuration.ConfigurationEx later
    config.config = opts

    rucioTransfer = RucioTransferMain()

    rucioTransfer.run()


if __name__ == "__main__":
    main()
