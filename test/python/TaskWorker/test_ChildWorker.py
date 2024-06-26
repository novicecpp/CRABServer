import time
import pytest
import ctypes
from argparse import Namespace
from unittest.mock import Mock

from WMCore.Configuration import ConfigurationEx
from TaskWorker.ChildWorker import startChildWorker
from TaskWorker.WorkerExceptions import ChildUnexpectedExitException, ChildTimeoutException



@pytest.fixture
def config_ChildWorker():
    config = ConfigurationEx()
    config.section_("TaskWorker")
    config.TaskWorker.childWorkerTimeout = 1
    return config

@pytest.fixture
def mock_logger():
    logger = Mock()
    logger.name = '1'
    return logger

def fn(n, timeSleep=0, mode='any'):
    print(f'executing function with n={n},timeSleep={timeSleep},mode={mode}')
    if mode == 'timeout':
        time.sleep(timeSleep)
    elif mode == 'exception':
        raise TypeError('simulate raise generic exception')
    elif mode == 'coredump':
        #https://codegolf.stackexchange.com/a/22383
        ctypes.string_at(1)
    else:
        pass
    return n*5


def test_startChildWorker_normal(config_ChildWorker, mock_logger):
    n = 17
    timeSleep = 0
    mode = 'any'
    startChildWorker(config_ChildWorker, fn, (n, timeSleep, mode), mock_logger)


testList = [
    (17, 0, 'any', None),
    (17, 0, 'exception', TypeError),
    (17, 5, 'timeout', ChildTimeoutException),
    (17, 0, 'coredump', ChildUnexpectedExitException),
]
@pytest.mark.parametrize("n, timeSleep, mode, exceptionObj", testList)
def test_executeTapeRecallPolicy_allow(n, timeSleep, mode, exceptionObj, config_ChildWorker, mock_logger):
    if not exceptionObj:
        startChildWorker(config_ChildWorker, fn, (n, timeSleep, mode), mock_logger)
    else:
        with pytest.raises(exceptionObj):
            startChildWorker(config_ChildWorker, fn, (n, timeSleep, mode), mock_logger)
