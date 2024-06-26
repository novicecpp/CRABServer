"""
Fork process to run a function inside child process
This to prevent the worker process get stuck or die without master notice.
Leverage concurrent.futures.ProcessPoolExecutor to fork process with single
process, return value back or propargate exception from child process
to caller.

The startChildWorker() can handle coredump, timeout, and generic exception.

Original issue: https://github.com/dmwm/CRABServer/issues/8428
"""

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import multiprocessing as mp
import signal
import logging
from TaskWorker.WorkerExceptions import ChildUnexpectedExitException, ChildTimeoutException


def startChildWorker(config, work, workArgs, logger):
    """
    Public function to run any function in child-worker.

    :param config: crab configuration object
    :type config: WMCore.Configuration.ConfigurationEx
    :param work: a function that need to run in child process
    :type work: function
    :param workArgs: tuple of arguments of `work()`
    :type workArgs: tuple
    :param logger: log object
    :param logger: logging.Logger

    :returns: return value from `work()`
    :rtype: any
    """
    procTimeout = config.FeatureFlags.childWorkerTimeout
    with ProcessPoolExecutor(max_workers=1, mp_context=mp.get_context('spawn')) as executor:
        future = executor.submit(_runChildWorker, work, workArgs, procTimeout, logger)
        try:
            outputs = future.result(timeout=procTimeout+1)
        except BrokenProcessPool as e:
            raise ChildUnexpectedExitException('Child process exited unexpectedly.') from e
        except TimeoutError as e:
            raise ChildTimeoutException(f'Child process timeout reached (timeout {procTimeout} seconds).') from e
        except Exception as e:
            raise e
    return outputs

def _signalHandler(signum, frame):
    """
    Simply raise timeout exception and let ProcessPoolExecutor propagate error
    back to parent process.
    Boilerplate come from https://docs.python.org/3/library/signal.html#examples
    """
    raise TimeoutError("The process reached timeout.")

def _runChildWorker(work, workArgs, timeout, logger):
    """
    The wrapper function to start running `work()` on the child-worker. It
    install SIGALARM with `timeout` to stop processing current work and raise
    TimeoutError when timeout is reach.

    Note about `logger` object. It works out of the box because:
    - Parent process are stop and wait until this function return.
    - Fd

    :param work: a function that need to run in child process
    :type work: function
    :param workArgs: tuple of arguments of `work()`
    :type workArgs: tuple
    :param timeout: function call timeout in seconds
    :type timeout: int
    :param loggerConfig: logger configuration
    :param loggerConfig: dict

    :returns: return value from `work()`
    :rtype: any
    """

    # main
    logger.debug(f'Installing SIGALARM with timeout {timeout} seconds.')
    signal.signal(signal.SIGALRM, _signalHandler)
    signal.alarm(timeout)
    outputs = work(*workArgs)
    logger.debug('Uninstalling SIGALARM.')
    signal.alarm(0)
    return outputs
