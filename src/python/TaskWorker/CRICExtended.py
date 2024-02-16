from WMCore.Services.CRIC.CRIC import CRIC


class CRICExtended(CRIC):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__(*args, **kwargs)

    def _CRICGroupQuery(self, callname, groupname):
        """
        """

        uri = "/api/accounts/group/query/"
        args = {"name": groupname}
        groupinfo = self._getResult(uri, callname=callname, args=args, unflatJson=False)
        return groupinfo

    def listUserInGroup(self, groupname):
        """
        cms-crab-HighPrioUsers
        https://cms-cric.cern.ch/api/accounts/group/query/?json&name=CMS_CRAB_HighPrioUsers&preset=default
        """
        groupinfo = self._CRICGroupQuery('default', groupname)
        import pdb; pdb.set_trace()
        Exception()
        return
