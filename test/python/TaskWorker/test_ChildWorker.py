from argparse import Namespace
import time
import pytest

from WMCore.Configuration import ConfigurationEx
from TaskWorker.ChildWorker import startChildWorker
from TaskWorker.WorkerExceptions import ChildUnexpectedExitException, ChildTimeoutException



@pytest.fixture
def config_ChildWorker():
    config = ConfigurationEx()
    config.section_("TaskWorker")
    config.TaskWorker.childWorkerTimeout = 1
    return config

def fn(n, timeSleep=1):
    print(f'executing function with n={n},timeSleep={timeSleep}')
    time.sleep(timeSleep)
    print(f'return {n}*5')
    return n*5

def test_startChildWorker_normal():
    pass
def test_startChildWorker_exception():
    pass
