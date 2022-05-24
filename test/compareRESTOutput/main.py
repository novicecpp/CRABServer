import os
import sys
import logging
import pprint
from RESTInteractions import CRABRest
from urllib.parse import urlparse, parse_qs

X509_USER_PROXY = os.environ['X509_USER_PROXY']
USER_AGENT = os.environ.get('USER_AGENT', 'CRABTest')
DATABASE_INSTANCE = os.environ.get('DATABASE_INSTANCE', 'prod')


logger = logging.getLogger('CRABTest')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel('DEBUG')

def create_requests(list_request_str):
    ret = []
    for s in list_request_str.split('\n'):
        if s.strip() == '':
            continue
        elif s.strip().startswith('#'):
            continue
        method, request = s.split(' ')
        url = urlparse(s)
        api = url.path.split('/')[-1]
        data = parse_qs(url.query)
        ret.append({'method': method, 'api': api, 'data': data})
    return ret


def main():
    with open(sys.argv[1], 'r') as r:
        requests = create_requests(r.read())
    crabserver_prod = CRABRest(hostname='cmsweb.cern.ch',
                               localcert=X509_USER_PROXY,
                               localkey=X509_USER_PROXY,
                               userAgent=USER_AGENT,
                               logger=logger,
                               version='0.0.0')
    crabserver_prod.setDbInstance('prod')
    crabserver_dev = CRABRest(hostname='cmsweb-test11.cern.ch',
                              localcert=X509_USER_PROXY,
                              localkey=X509_USER_PROXY,
                              userAgent=USER_AGENT,
                              logger=logger,
                              version='0.0.0')
    crabserver_dev.setDbInstance('prod')
    for r in requests:
        logger.debug(f"Retrieving {r['method']} /{r['api']} from dev.")
        dev_result = crabserver_dev.get(r['api'], r['data'])[0]
        logger.debug(f"Retrieving {r['method']} /{r['api']} from prod.")
        prod_result = crabserver_prod.get(r['api'], r['data'])[0]
        compare_result = prod_result == dev_result
        logger.info(f"{r['method']} {r['api']} compare result: {compare_result}")
        if compare_result:
            logger.debug(f"\nprod value:\n{pprint.pformat(prod_result)}\n\ndev value:\n{pprint.pformat(dev_result)}")
            sys.exit(1)
        else:
            logger.error(f"result from prod and dev is not equal. See output below")
            logger.error(f"\nprod value:\n{pprint.pformat(prod_result)}\n\ndev value:\n{pprint.pformat(dev_result)}")
            sys.exit(1)


if __name__ == '__main__':
    main()
