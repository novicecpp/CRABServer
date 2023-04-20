from ServerUtilities import encodeRequest

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
