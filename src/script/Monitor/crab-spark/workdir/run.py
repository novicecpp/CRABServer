#!/usr/bin/env python3
import argparse
import os
import subprocess
import pathlib
from pprint import pprint
from datetime import datetime, timedelta, timezone

def valid_date(s):
    try:
        return s
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a valid date: {s!r}")

parser = argparse.ArgumentParser(description='crab service process controller')
parser.add_argument('path', help='')
parser.add_argument('--start', type=valid_date, dest='start_date', help='')
parser.add_argument('--end', type=valid_date, dest='end_date', help='')
parser.add_argument('--today', action='store_true', help='')
parser.add_argument('--ndaysago', type=int, default=-1, help='')
parser.add_argument('--prod', action='store_true', help='')
parser.add_argument('--secretpath', help='')
parser.add_argument('--dryrun', action='store_true', help='')
args = parser.parse_args()

sparkjob_env = {}
if args.today:
    args.ndaysago = 0
if args.ndaysago >= 0:
    day = datetime.now().replace(tzinfo=timezone.utc)
    ed = args.ndaysago
    sd = args.ndaysago + 1 # start date is "yesterday" of n days ago
    sparkjob_env['START_DATE'] = (day-timedelta(days=sd)).strftime("%Y-%m-%d")
    sparkjob_env['END_DATE'] = (day-timedelta(days=ed)).strftime("%Y-%m-%d")
if args.start_date and args.end_date:
    sparkjob_env['START_DATE'] = args.start_date
    sparkjob_env['END_DATE'] = args.end_date
if 'START_DATE' not in sparkjob_env and 'END_DATE' not in sparkjob_env:
    raise Exception("Need --today or --ndaysago or --start/--end.")
if args.secretpath:
    sparkjob_env['OPENSEARCH_SECRET_PATH'] = args.secretpath
if args.prod:
    sparkjob_env['PROD'] = 't'
else:
    sparkjob_env['PROD'] = 'f'

runenv = os.environ.copy()
runenv.update(sparkjob_env)

path = pathlib.Path(args.path)
pathpy = path.with_suffix('.py')
cmd = f"jupyter nbconvert --to python {path}"
print(f'Running: {cmd}')
if not args.dryrun:
    subprocess.run(cmd, shell=True, timeout=3600, check=True)

cmd = f'spark-submit --master yarn --packages org.apache.spark:spark-avro_2.12:3.5.0 {pathpy}'
print(f'Running: {cmd}')
print('With env: ')
pprint(sparkjob_env)
if not args.dryrun:
    subprocess.run(cmd, shell=True, timeout=3600, check=True, env=runenv)
