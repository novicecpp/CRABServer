import shutil
import re
from contextlib import contextmanager

from ServerUtilities import encodeRequest
from ASO.Rucio.exception import RucioTransferException

@contextmanager
def writePath(path):
    """
    Prevent bookkeeping file corruption by simply write to temp file and replace
    original file.

    This simple contextmanager provide new io object for file write operation
    to `path` with `_tmp` suffix. At the end of `with` statement it will
    replace original path with temp file.

    :param path: path to write.
    :yield: `_io.TextIOWrapper` object for write operation.
    """
    tmpPath = f'{path}_tmp'
    with open(tmpPath, 'w', encoding='utf-8') as w:
        yield w
    shutil.move(tmpPath, path)


def chunks(lst: list = None, n: int = 1):
    """
    Yield successive n-sized chunks from l.
    :param l: list to splitt in chunks
    :param n: chunk size
    :return: yield the next list chunk
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def updateDB(client, api, subresource, fileDoc, logger=None):
    fileDoc['subresource'] = subresource
    client.post(
        api=api,
        data=encodeRequest(fileDoc)
    )

def tfcLFN2PFN(lfn, tfc, proto, depth=0):
    # Hardcode
    MAX_CHAIN_DEPTH = 5
    if depth > MAX_CHAIN_DEPTH:
        raise RucioTransferException(f"Max depth reached matching lfn {lfn} and protocol {proto} with tfc {tfc}")
    for rule in tfc:
        if rule['proto'] == proto:
            if 'chain' in rule:
                import pdb; pdb.set_trace()
                lfn = tfcLFN2PFN(lfn, tfc, rule['chain'], depth + 1)
            regex = re.compile(rule['path'])
            if regex.match(lfn):
                return regex.sub(rule['out'].replace('$', '\\'), lfn)
    if depth > 0:
        return lfn
    raise ValueError(f"lfn {lfn} with proto {proto} cannot be matched by tfc {tfc}")
