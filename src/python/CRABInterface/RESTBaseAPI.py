from __future__ import absolute_import
import logging

import cherrypy
from cherrypy import request
import time
from subprocess import getstatusoutput
from time import mktime, gmtime

# WMCore dependecies here
from WMCore.REST.Server import DatabaseRESTApi, rows
from WMCore.REST.Format import JSONFormat
from WMCore.REST.Error import ExecutionError

# CRABServer dependecies here
from CRABInterface.Utilities import ConfigCache, globalinit, getCentralConfig
from CRABInterface.RESTUserWorkflow import RESTUserWorkflow
from CRABInterface.RESTTask import RESTTask
from CRABInterface.RESTServerInfo import RESTServerInfo
from CRABInterface.RESTFileMetadata import RESTFileMetadata
from CRABInterface.RESTFileTransfers import RESTFileTransfers
from CRABInterface.RESTFileUserTransfers import RESTFileUserTransfers
from CRABInterface.RESTWorkerWorkflow import RESTWorkerWorkflow
from CRABInterface.RESTCache import RESTCache
from CRABInterface.DataFileMetadata import DataFileMetadata
from CRABInterface.DataWorkflow import DataWorkflow
from CRABInterface.DataUserWorkflow import DataUserWorkflow
from ServerUtilities import get_size

#In case the log level is not specified in the configuration we use the NullHandler and we do not print messages
#The NullHandler is included as of python 3.1
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

class RESTBaseAPI(DatabaseRESTApi):
    """The CRABServer REST API modules"""

    def __init__(self, app, config, mount):
        DatabaseRESTApi.__init__(self, app, config, mount)

        self.formats = [ ('application/json', JSONFormat()) ]

        extconfig = ConfigCache(centralconfig=getCentralConfig(extconfigurl=config.extconfigurl, mode=config.mode),
                                      cachetime=mktime(gmtime()))

        #Global initialization of Data objects. Parameters coming from the config should go here
        DataUserWorkflow.globalinit(config)
        DataWorkflow.globalinit(dbapi=self, credpath=config.credpath, centralcfg=extconfig, config=config)
        DataFileMetadata.globalinit(dbapi=self, config=config)
        RESTTask.globalinit(centralcfg=extconfig)
        globalinit(config.credpath)

        ## TODO need a check to verify the format depending on the resource
        ##      the RESTFileMetadata has the specifc requirement of getting xml reports
        self._add( {'workflow': RESTUserWorkflow(app, self, config, mount, extconfig),
                    'info': RESTServerInfo(app, self, config, mount, extconfig),
                    'filemetadata': RESTFileMetadata(app, self, config, mount),
                    'workflowdb': RESTWorkerWorkflow(app, self, config, mount),
                    'task': RESTTask(app, self, config, mount),
                    'filetransfers': RESTFileTransfers(app, self, config, mount),
                    'fileusertransfers': RESTFileUserTransfers(app, self, config, mount),
                   })
        cacheSSL = extconfig.centralconfig['backend-urls']['cacheSSL']
        if 'S3' in cacheSSL.upper():
            self._add({'cache': RESTCache(app, self, config, mount, extconfig)})

        self._initLogger( getattr(config, 'loggingFile', None), getattr(config, 'loggingLevel', None),
                          getattr(config, 'keptLogDays', 0))

    def modifynocheck(self, sql, *binds, **kwbinds):
        """This is the same as `WMCore.REST.Server`:modify method but
           not implementing any kind of checks on the number of modified
           rows.

        :arg str sql: SQL modify statement.
        :arg list binds: Bind variables by position: list of dictionaries.
        :arg dict kwbinds: Bind variables by keyword: dictionary of lists.
        :result: See :meth:`rowstatus` and description in `WMCore.REST.Server`."""
        if binds:
            c, _ = self.executemany(sql, *binds, **kwbinds)
        else:
            kwbinds = self.bindmap(**kwbinds)
            c, _ = self.executemany(sql, kwbinds, *binds)
        trace = cherrypy.request.db["handle"]["trace"]
        trace and cherrypy.log("%s commit" % trace)  # pylint: disable=expression-not-assigned
        cherrypy.request.db["handle"]["connection"].commit()
        return rows([{ "modified": c.rowcount }])

    def execute(self, sql, *binds, **kwbinds):
        """override execute function and logging time use at cursor().execute()
        """
        c = self.prepare(sql)
        trace = request.db["handle"]["trace"]
        request.db["last_bind"] = (binds, kwbinds)
        trace and cherrypy.log("%s execute: %s %s" % (trace, binds, kwbinds))
        if request.db['type'].__name__ == 'MySQLdb':
            return c, c.execute(sql, kwbinds)
        st = time.time()
        ret = c.execute(None, *binds, **kwbinds)
        ed = time.time() - st
        cherrypy.log("execute time: %6f" % (ed,))
        return c, ret

    def executemany(self, sql, *binds, **kwbinds):
        """same as execute()"""

        c = self.prepare(sql)
        trace = request.db["handle"]["trace"]
        request.db["last_bind"] = (binds, kwbinds)
        trace and cherrypy.log("%s executemany: %s %s" % (trace, binds, kwbinds))
        if request.db['type'].__name__ == 'MySQLdb':
            return c, c.executemany(sql, binds[0])
        st = time.time()
        ret = c.executemany(None, *binds, **kwbinds)
        ed = time.time() - st
        cherrypy.log("executemany time: %6f" % (ed,))
        return c, ret

    def query_load_all_rows(self, match, select, sql, *binds, **kwbinds):
        st = time.time()
        ret = list(super().query(match, select, sql, *binds, **kwbinds))
        ep = time.time() - st
        size = get_size(ret)
        cherrypy.log('query time: %6f, size %6f' % (ep, size))
        return iter(ret) # return iterable object

    def _initLogger(self, logfile, loglevel, keptDays=0):
        """
        Setup the logger for all the CRAB API's. If loglevel is not specified (==None) we use the NullHandler which just 'pass' and does not log

        RESTEntities and other parts of the code can retrieve it by calling: logging.getLogger('CRABLogger.ChildName')
        ChildName is the specific name of the logger (child of CRABLogger). Using childs in that way we can configure
        the logging in a flexible way (a module logs at DEBUG level to a file, another module logs at INFO level to stdout, etc)
        """
        import logging.handlers
        logger = logging.getLogger('CRABLogger')
        if loglevel:
            hdlr = logging.handlers.TimedRotatingFileHandler(logfile, when='D', interval=1, backupCount=keptDays)
            formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
            logger.setLevel(loglevel)
        else:
            logger.addHandler( NullHandler() )
