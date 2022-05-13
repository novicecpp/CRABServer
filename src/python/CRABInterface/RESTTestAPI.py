import logging

# WMCore dependecies here
from WMCore.REST.Server import RESTEntity, restcall
from WMCore.REST.Validation import validate_str

# CRABServer dependecies here
from CRABInterface.RESTExtensions import authz_login_valid
from CRABInterface.Regexps import RX_SUBRES_SI, RX_TASKNAME
import time
import random


class RESTTestAPI(RESTEntity):
    """REST entity for workflows and relative subresources"""

    def __init__(self, app, api, config, mount, centralcfg):
        RESTEntity.__init__(self, app, api, config, mount)
        self.centralcfg = centralcfg
        self.logger = logging.getLogger("CRABLogger:RESTTestAPI")
        #used by the client to get the url where to update the cache (cacheSSL)

    def validate(self, apiobj, method, api, param, safe):
        """Validating all the input parameter as enforced by the WMCore.REST module"""
        authz_login_valid()
        #if method in ['GET']:
        #    validate_str('subresource', param, safe, RX_SUBRES_SI, optional=True)
        #    validate_str('workflow', param, safe, RX_TASKNAME, optional=True)

    @restcall
    def get(self, **kwargs):
        """Retrieves the server information, like delegateDN, filecacheurls ...
           :arg str subresource: the specific server information to be accessed;
        """
        randnum = random.uniform(10.5, 75.5)
        time.sleep(randnum)
        return [{"crabserver":"Welcome","randnum": randnum}]
