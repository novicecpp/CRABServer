import os
import sys
import logging
import hashlib
import json
import pprint
import argparse
from RESTInteractions import CRABRest
from urllib.parse import urlparse, parse_qs


logger = logging.getLogger('CRABTest')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def create_requests_from_file(path):
    """read list of request from file and convert it to object
    content of file are consist of GET request string seperate by newline
    e.g /crabserver/prod/info?subresource=version
    comment with # is supported

    return list of dict
    """
    with open(path, 'r') as r:
        list_request_raw = r.readlines()
    ret = []
    for s in list_request_raw:
        if s.strip() == '' or s.strip().startswith('#'):
            continue
        request = s.strip()
        url = urlparse(s)
        api = url.path.split('/')[-1]
        data = parse_qs(url.query)
        request = {'request': request,
                   'request_hash': hashlib.md5(request.encode()).hexdigest(),
                   'api': api,
                   'data': data}
        ret.append(request)
    return ret

def create(requests, output_dir, restclient):
    """get output from request list and dump it out to file
    """
    for request in requests:
        output_path = os.path.join(output_dir, request['request_hash']) + '.json'
        logger.debug(f"Retrieving GET /{request['api']}")
        output = restclient.get(request['api'], request['data'])[0]
        with open(output_path, 'w') as w:
            json.dump(output, w)

def compare(requests, input_dir, rest_client):
    """compare output from request list with json
    """
    for request in requests:
        logger.debug(f"Retrieving GET /{request['api']}")
        server_output = crabserver.get(request['api'], request['data'])[0]
        with open(os.path.join(input_dir, request['request_hash'] + '.json'), 'r') as r:
            expected_output = json.load(r)
        compare_result = server_output == expected_output
        logger.info(f"GET /{request['api']} compare result: {compare_result}")
        if compare_result:
            logger.debug("\nServer output:\n%s\n\nexpected output:\n%s", pprint.pformat(server_output), pprint.pformat(expected_output))
        else:
            logger.error("Result from server and expected file is equal. See output below")
            logger.debug(f"\nServer output:\n{pprint.pformat(server_output)}\n\nexpected output:\n{pprint.pformat(expected_output)}")
            sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=__file__)
    parser.add_argument('mode', type=str, help='mode')
    parser.add_argument('url_path', type=str, help='url file path')
    parser.add_argument('--db',
                        type=str,
                        default=os.getenv('DATABASE_INSTANCE', 'devtwo'),
                        help='database instance (dev/devtwo/preprod/prod')
    parser.add_argument('--rest',
                        type=str,
                        default=os.getenv('CRABSERVER_HOSTNAME', 'cmsweb-test11.cern.ch'),
                        help='rest hostname e.g. cmsweb-test11.cern.ch.')
    parser.add_argument('--userproxy',
                        type=str,
                        default=os.getenv('X509_USER_PROXY', '/tmp/cert.pem'),
                        help='user proxy file path')
    parser.add_argument('--loglevel',
                        type=str,
                        default='INFO',
                        help='log level (uppercase)')
    args = parser.parse_args()

    logger.setLevel(args.loglevel)
    logger.info("%s", args)

    requests = create_requests_from_file(args.url_path)
    crabserver = CRABRest(hostname=args.rest,
                          localcert=args.userproxy,
                          localkey=args.userproxy,
                          userAgent='CRABRest',
                          logger=logger,
                          version='0.0.0')
    crabserver.setDbInstance(args.db)
    if args.mode == 'create':
        create(requests, os.path.dirname(args.url_path), crabserver)
    if args.mode == 'compare':
        compare(requests, os.path.dirname(args.url_path), crabserver)
