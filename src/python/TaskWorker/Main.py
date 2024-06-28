from optparse import OptionParser
import signal
import os
import logging

from WMCore.Configuration import loadConfigurationFile
from TaskWorker.WorkerExceptions import ConfigException
from TaskWorker.MasterWorker import MasterWorker

def validateConfig(config):
    """Verify that the input configuration contains all needed info

    :arg WMCore.Configuration config: input configuration
    :return bool, string: flag for validation result and a message."""
    if getattr(config, 'TaskWorker', None) is None:
        return False, "Configuration problem: Task worker section is missing. "
    if not hasattr(config.TaskWorker, 'scheddPickerFunction'):
        config.TaskWorker.scheddPickerFunction = HTCondorLocator.memoryBasedChoices
    return True, 'Ok'

def main():
    usage = "usage: %prog [options] [args]"
    parser = OptionParser(usage=usage)

    parser.add_option("-d", "--logDebug",
                      action="store_true",
                      dest="logDebug",
                      default=False,
                      help="print extra messages to stdout")
    parser.add_option("-w", "--logWarning",
                      action="store_true",
                      dest="logWarning",
                      default=False,
                      help="don't print any messages to stdout")
    parser.add_option("-s", "--sequential",
                      action="store_true",
                      dest="sequential",
                      default=False,
                      help="run in sequential (no subprocesses) mode")
    parser.add_option("-c", "--console",
                      action="store_true",
                      dest="console",
                      default=False,
                      help="log to console")

    parser.add_option("--config",
                      dest="config",
                      default=None,
                      metavar="FILE",
                      help="configuration file path")

    (options, args) = parser.parse_args()


    if not options.config:
        raise ConfigException("Configuration not found")

    configuration = loadConfigurationFile(os.path.abspath(options.config))
    status_, msg_ = validateConfig(configuration)
    if not status_:
        raise ConfigException(msg_)

    if options.sequential:
        # override root loglevel to debug
        logging.getLogger().setLevel(logging.DEBUG)
        # need for single thread
        configuration.TaskWorker.nslaves = 1
        configuration.FeatureFlags.childWorker = False
        # start with pdb
        import pdb #pylint: disable=import-outside-toplevel
        pdb.set_trace()
        mc = MasterWorker(config=configuration, logWarning=False, logDebug=True, sequential=True, console=True)
        mc.algorithm()
        return 0

    mw = None
    try:
        mw = MasterWorker(configuration, logWarning=options.logWarning, logDebug=options.logDebug, sequential=options.sequential, console=options.console)
        signal.signal(signal.SIGINT, mw.quit_)
        signal.signal(signal.SIGTERM, mw.quit_)
        mw.algorithm()
    except:
        if mw:
            mw.logger.exception("Unexpected and fatal error. Exiting task worker")
        #don't really wanna miss this, propagating the exception and exiting really bad
        raise
    finally:
        #there can be an exception before slaves are created, e.g. in the __init__
        if hasattr(mw, 'slaves'):
            mw.slaves.end()
