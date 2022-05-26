import logging

# WMCore dependecies here
from WMCore.REST.Server import RESTEntity, restcall
from WMCore.REST.Validation import validate_str
from cherrypy import request

# CRABServer dependecies here
from CRABInterface.RESTExtensions import authz_login_valid
from CRABInterface.Regexps import RX_SUBRES_SI, RX_TASKNAME
import time
import random


class RESTTestAPI(RESTEntity):
    """REST entity for workflows and relative subresources"""

    def __init__(self, app, api, config, mount):
        RESTEntity.__init__(self, app, api, config, mount)
        self.logger = logging.getLogger("CRABLogger.RESTTestAPI")
        f = TestFilter()
        self.logger.addFilter(f)

    def validate(self, apiobj, method, api, param, safe):
        """Validating all the input parameter as enforced by the WMCore.REST module"""
        authz_login_valid()
        if method in ['GET']:
            validate_str('subresource', param, safe, RX_SUBRES_SI, optional=True)
        #    validate_str('workflow', param, safe, RX_TASKNAME, optional=True)

    @restcall
    def get(self, subresource, **kwargs):
        """Retrieves the server information, like delegateDN, filecacheurls ...
           :arg str subresource: the specific server information to be accessed;
        """
        #import pdb; pdb.set_trace()
        self.logger.info('testlog trace=%s', request.request_trace_id)
        if subresource == 'exception':
            raise Exception('test raise exception in crab code')
        else:
            ret = [{"crabserver":"Welcome to himalaya"}]
            return ret

import cherrypy
import logging

class TestFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = cherrypy.request.request_trace_id
        return True
