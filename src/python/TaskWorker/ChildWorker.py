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
    # we cannot passing the logger object to child worker.
    loggerConfig = {
        'name': logger.name,
        # hardcode formatter to make in more simple. The format is copied from:
        # https://github.com/dmwm/CRABServer/blob/43a8454abec4059ae5b2804b4efe8e77553d1f38/src/python/TaskWorker/Worker.py#L30
        'format': "%(asctime)s:%(levelname)s:%(module)s %(message)s",
        # also hardcode the log level
        'level': logging.DEBUG,
    }
    with ProcessPoolExecutor(max_workers=1, mp_context=mp.get_context('fork')) as executor:
        future = executor.submit(_runChildWorker, work, workArgs, procTimeout, loggerConfig)
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

def _runChildWorker(work, workArgs, timeout, loggerConfig):
    """
    The wrapper function to start running `work()` on the child-worker.

    Note about loggerName argument, logging object cannot be pickled so we pass
    the logging configuration and set it up on child-worker side.

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
    logger = logging.getLogger(f'{loggerConfig["name"]}.ChildWorker')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(loggerConfig['format']))
    logger.addHandler(handler)
    logger.setLevel(loggerConfig['level'])
    logger.info(f'Installing SIGALARM with timeout {timeout} seconds.')
    signal.signal(signal.SIGALRM, _signalHandler)
    signal.alarm(timeout)
    outputs = work(*workArgs)
    signal.alarm(0)
    return outputs
