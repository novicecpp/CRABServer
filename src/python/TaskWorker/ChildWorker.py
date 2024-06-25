from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from TaskWorker.WorkerExceptions import ChildUnexpectedExitException, ChildTimeoutException
import multiprocessing as mp
import signal
import traceback
import logging


def startChildWorker(config, work, workArgs, logger):
    procTimeout = getattr(config.TaskWorker, 'childWorkerTimeout', 120)
    loggerName = logger.name
    work = work
    workArgs = workArgs
    with ProcessPoolExecutor(max_workers=1, mp_context=mp.get_context('forkserver')) as executor:
        future = executor.submit(runChildWorker, work, workArgs, procTimeout, loggerName)
        try:
            outputs = future.result(timeout=procTimeout+1)
        except BrokenProcessPool as e:
            raise ChildUnexpectedExitException('Child process exit unexpectedly.') from e
        except TimeoutError as e:
            raise ChildTimeoutException(f'Child process timeout reached (timeout {procTimeout} seconds).')
        except Exception as e:
            raise e
    return outputs

def _signalHandler(signum, frame):
     raise TimeoutError(f"The process reached timeout.")

def runChildWorker(work, workArgs, timeout, loggerName):
    logger = logging.getLogger(f'{loggerName}.childprocess')
    logger.info(f'Installing SIGALARM with timeout {timeout}')
    signal.signal(signal.SIGALRM, _signalHandler)
    signal.alarm(timeout)
    outputs = work(*workArgs)
    signal.alarm(0)
    return outputs
