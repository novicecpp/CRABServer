"""
Manages recurring actions for tape recall functionalities
1. for tasks in TAPERECALL check status of rule and set to NEW when rule is OK
2. for tasks in KILLRECALL delete rule and set to KILLED
"""
import logging
import sys
import os
import time
import copy

from urllib.parse import urlencode

from rucio.common.exception import RuleNotFound

from ServerUtilities import MAX_DAYS_FOR_TAPERECALL, getTimeFromTaskname
from RESTInteractions import CRABRest
from RucioUtils import getNativeRucioClient
from CRABUtils.TaskUtils import uploadWarning, deleteWarnings, updateTaskStatus, getTasks
from TaskWorker.MasterWorker import getRESTParams
from TaskWorker.Worker import failTask
from TaskWorker.Actions.Recurring.BaseRecurringAction import BaseRecurringAction


class TapeRecallManager(BaseRecurringAction):
    """ interface needed by the way TW deals with recurring actions
    must have a class which inherit from BaseRecurringAction
    which implements the _execute method (with the unused argument "task"...pff)
    name of this class, this file and the recurring action in TW config list
    must be the same """
    pollingTime = 60 * 2  # unit=minutes. Runs every 2 hours
    # some static class variables to prevent pylint W0201
    rucioClient = None
    privilegedRucioClient = None
    crabserver = None
    config = None
    restHost = None
    dbInstance = None

    def _execute(self, config, task):  # pylint: disable=unused-argument, invalid-name
        """ this is what we do at every polling cycle """
        self.config = config
        # setup logger, crabserver client, rucio client
        self.init()
        # do the work
        self.handleRecall()
        self.handleKill()

    def handleKill(self):
        """ looks for tasks in KILLRECALL and deals with them """
        status = 'KILLRECALL'
        tasksToWorkOn = getTasks(crabserver=self.crabserver, status=status, logger=self.logger)

        for aTask in tasksToWorkOn:
            taskName = aTask['tm_taskname']
            msg = f"Working on task {taskName}"
            self.logger.info(msg)

            reqId = aTask['tm_DDM_reqid']
            if not reqId:
                msg = f"tm_DDM_reqid' is not defined for task {taskName}, skipping it"
                self.logger.debug(msg)
                # leave the task in there, so that in time it gets noticed and the issue addressed
                continue
            msg = f"Task points to Rucio RuleId:  {reqId} "
            self.logger.info(msg)

            # delete rule and set task status to killed
            # Check if this rule can be deleted. Is any other task using it ?
            tasksUsingThisRule = self.findTasksForRule(ruleId=reqId)
            if len(tasksUsingThisRule) == 1 and tasksUsingThisRule[0] == taskName:
                msg = f"Will delete rule {reqId}"
                self.logger.info(msg)
                try:
                    # suspend rule first to avoid more FTS submissions while delete daemon kicks in
                    self.privilegedRucioClient.update_replication_rule(rule_id=reqId,
                                                                       options={'state':'SUSPENDED'})
                    self.privilegedRucioClient.delete_replication_rule(reqId)
                except RuleNotFound:
                    self.logger.info("Rule not found, can not delete it. Simply set task as KILLED")
            else:
                msg = f"rule {reqId} used by tasks {tasksUsingThisRule}. Will not delete it"
                self.logger.info(msg)
            updateTaskStatus(crabserver=self.crabserver, taskName=taskName, status='KILLED', logger=self.logger)
            # Clean up previous "dataset on tape" warnings
            deleteWarnings(crabserver=self.crabserver, taskname=taskName, logger=self.logger)
            self.logger.info("Done on this task")

    def handleRecall(self):
        """ looks for tasks in TAPERECALL and deals with them """
        status = 'TAPERECALL'
        tasksToWorkOn = getTasks(crabserver=self.crabserver, status=status, logger=self.logger)

        for aTask in tasksToWorkOn:
            taskName = aTask['tm_taskname']
            msg = f"Working on task {taskName}"
            self.logger.info(msg)
            # 1.) check for "waited too long"
            waitDays = int((time.time() - getTimeFromTaskname(str(taskName))) // 3600 // 24)  # from sec to days
            if waitDays > MAX_DAYS_FOR_TAPERECALL:
                msg = f"Tape recall request did not complete in {MAX_DAYS_FOR_TAPERECALL} days."
                self.logger.info(msg)
                failTask(taskName, self.crabserver, msg, self.logger, 'FAILED')
                # there is no need to remove the rule since it will expire after
                # last task requesting those data was submitted.
                continue
            # 2.) integrity checks
            reqId = aTask['tm_DDM_reqid']
            if not reqId:
                self.logger.debug("tm_DDM_reqid' is not defined for task %s, skipping it", taskName)
                continue
            msg = f"Task points to Rucio RuleId:  {reqId}"
            self.logger.info(msg)
            try:
                rule = self.rucioClient.get_replication_rule(reqId)
            except RuleNotFound:
                msg = f"Rucio rule id {reqId} not found. Please report to experts"
                self.logger.error(msg)
                uploadWarning(crabserver=self.crabserver, taskname=taskName, msg=msg, logger=self.logger)
                continue
            msg = f"Rule {reqId} is {rule['state']}"
            self.logger.info(msg)
            # 3.) check if rule completed
            if rule['state'] == 'OK':
                # all good kick off a new processing
                msg = f"Request {reqId} is completed, proceed with submission"
                self.logger.info(msg)
                updateTaskStatus(crabserver=self.crabserver, taskName=taskName, status='NEW', logger=self.logger)
                # Clean up previous "dataset on tape" warnings
                deleteWarnings(crabserver=self.crabserver, taskname=taskName, logger=self.logger)
                # Make sure data will stay on disk for NOW + 4 days. A new rule will kick in when task is submitted
                self.logger.info("Extending rule lifetime to last 4 days")
                self.privilegedRucioClient.update_replication_rule(reqId, {'lifetime': (4 * 24 * 60 * 60)})  # lifetime is in seconds
            elif rule['state'] in ['REPLICATING', 'STUCK', 'SUSPENDED']:
                # in progress, report status and keep waiting
                ok = rule['locks_ok_cnt']
                rep = rule['locks_replicating_cnt']
                stuck = rule['locks_stuck_cnt']
                total = ok + rep + stuck
                okFraction = ok * 100 // total
                msg = f"Data recall from tape in progress: ok/all = {ok}/{total} = {okFraction}%"
                msg += f"\nRucio rule details at https://cms-rucio-webui.cern.ch/rule?rule_id={reqId}"
                enoughData = okFraction >= 99 or (rule['name'].endswith('SIM') and okFraction >= 90)
                if waitDays >= 7 and enoughData:
                    msg += (f"\nThis recall has lasted {waitDays} days already and it is >= {okFraction}% complete")
                    msg += ("\nYour needs are very likely to be satisfied with what's on disk now")
                    msg += ("\nSuggestion: kill this task and submit another one with config.Data.partialDataset=True")
                deleteWarnings(crabserver=self.crabserver, taskname=taskName, logger=self.logger)
                uploadWarning(crabserver=self.crabserver, taskname=taskName, msg=msg, logger=self.logger)
            self.logger.info("Done on this task")

    def init(self):
        """ setup logger, crabserver client and rucio client"""
        if not self.logger:
            # running interactively, setup logging to stdout
            self.logger = logging.getLogger(__name__)
            handler = logging.StreamHandler(sys.stdout)  # pylint: disable=redefined-outer-name
            formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s %(message)s")  # pylint: disable=redefined-outer-name
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            # do not use BaseRecurringAction logger but create a new logger
            # which writes to config.TaskWorker.logsDir/taks/recurring/TapeRecallManager_YYMMDD-HHMM.log
            self.logger = logging.getLogger('TapeRecallManager')
            logDir = self.config.TaskWorker.logsDir + '/tasks/recurring/'
            if not os.path.exists(logDir):
                os.makedirs(logDir)
            timeStamp = time.strftime('%y%m%d-%H%M', time.localtime())
            logFile = 'TapeRecallManager_' + timeStamp + '.log'
            handler = logging.FileHandler(logDir + logFile)
            formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # setup a crabserver REST client
        self.restHost, self.dbInstance = getRESTParams(self.config, self.logger)
        if not self.crabserver:
            self.crabserver = CRABRest(hostname=self.restHost, localcert=self.config.TaskWorker.cmscert,
                                       localkey=self.config.TaskWorker.cmskey,
                                       retry=2, userAgent='CRABTaskWorker')
            self.crabserver.setDbInstance(self.dbInstance)

        # setup a Rucio client
        if not self.rucioClient:
            self.rucioClient = getNativeRucioClient(config=self.config, logger=self.logger)

        # setup a Rucio client with the account which can edit our rules
        if not self.privilegedRucioClient:
            tapeRecallConfig = copy.deepcopy(self.config)
            tapeRecallConfig.Services.Rucio_account = 'crab_tape_recall'
            self.privilegedRucioClient = getNativeRucioClient(tapeRecallConfig, self.logger)

    def findTasksForRule(self, ruleId=None):
        """
        returns the list of task names which have stored the given Rucio
        rule as ddmreqid in DB Tasks table
        """
        # should this go in CRABUtils/TaskUtils.py ?
        data = {'subresource': 'taskbyddmreqid', 'ddmreqid': ruleId}
        res = self.crabserver.get(api='task', data=urlencode(data))
        tasks = res[0]['result']  # for obscure reasons this has the form [['task1'],['task2']...]
        taskList = [t[0] for t in tasks]
        return taskList


if __name__ == '__main__':
    # Simple main to execute the action standalone for testing
    # You just need to set the task worker environment and desired twconfig.

    TWCONFIG = '/data/srv/TaskManager/current/TaskWorkerConfig.py'

    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s %(message)s", datefmt="%a, %d %b %Y %H:%M:%S %Z(%z)")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    from WMCore.Configuration import loadConfigurationFile
    cfg = loadConfigurationFile(TWCONFIG)

    trm = TapeRecallManager(cfg.TaskWorker.logsDir)
    trm._execute(cfg, None)  # pylint: disable=protected-access
