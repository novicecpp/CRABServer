#! /usr/bin/env python
"""
The python helper to parse args
"""
import argparse
import os


class EnvDefault(argparse.Action):
    """
    # copy from https://stackoverflow.com/a/10551190
    # to be able to read from env if args not provided.
    """
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super().__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser(description='crab service process controller')

subparsers = parser.add_subparsers(dest='command', required=True)
parserStart = subparsers.add_parser('start')
groupModeStart = parserStart.add_mutually_exclusive_group(required=True)
groupModeStart.add_argument('-c', dest='mode', action='store_const', const='current')
groupModeStart.add_argument('-g', dest='mode', action='store_const', const='fromGH')
parserStart.add_argument('-d', dest='debug', action='store_const', const='t', default='f')
parserStart.add_argument('-s', dest='service', action=EnvDefault, envvar='SERVICE')
parserStop = subparsers.add_parser('stop')
parserEnv = subparsers.add_parser('env')
groupModeEnv = parserEnv.add_mutually_exclusive_group(required=True)
groupModeEnv.add_argument('-c', dest='mode', action='store_const', const='current')
groupModeEnv.add_argument('-g', dest='mode', action='store_const', const='fromGH')

args = parser.parse_args()

env = os.environ.copy()
# always provides env vars
env['COMMAND'] = args.command
env['MODE'] = getattr(args, 'mode', 'current')
env['DEBUG'] = getattr(args, 'debug', '')
env['SERVICE'] = getattr(args, 'service', '')

# re exec the ./manage.sh
os.execle('./manage.sh','./manage.sh', env)
