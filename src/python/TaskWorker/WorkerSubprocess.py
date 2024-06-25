from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from TaskWorker.WorkerExceptions import SlaveUnexpectedExitException
import signal
import traceback
import logging


def startSubprocess(config, work, workArgs, logger):
    procTimeout = getattr(config.TaskWorker, 'workerTimeout', 120)
    loggerName = logger.name
    work = work
    workArgs = workArgs
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(runSubprocess, work, workArgs, procTimeout, loggerName)
        try:
            outputs = future.result(timeout=procTimeout)
        except BrokenProcessPool as e:
            raise SlaveUnexpectedExitException('Slave exit unexpectedly.') from e
        except Exception as e:
            raise e
    return outputs

def _signalHandler(signum, frame):
     raise TimeoutError(f"The process reached timeout.")

def runSubprocess(work, workArgs, timeout, loggerName):
    logger = logging.getLogger(f'{loggerName}.childprocess')
    logger.info(f'Installing SIGALARM with timeout {timeout}')
    signal.signal(signal.SIGALRM, _signalHandler)
    signal.alarm(timeout)
    outputs = work(*workArgs)
    signal.alarm(0)
    return outputs
