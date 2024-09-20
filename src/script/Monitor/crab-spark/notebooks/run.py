#!/usr/bin/env python3
import argparse
import os
import subprocess
import pathlib

from datetime import datetime, timedelta

def valid_date(s):
    try:
        return s
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a valid date: {s!r}")

parser = argparse.ArgumentParser(description='crab service process controller')
parser.add_argument('path', help='')
parser.add_argument('--from', type=valid_date, dest='from_date', help='')
parser.add_argument('--to', type=valid_date, dest='to_date', help='')
parser.add_argument('--today', action='store_true', help='')
parser.add_argument('--prod', action='store_true', help='')
parser.add_argument('--secretpath', help='')
args = parser.parse_args()

sparkjob_env = os.environ.copy()
if args.today:
    day = datetime.now()
    sparkjob_env['FROM_DATE'] = day.strftime("%Y-%m-%d")
    sparkjob_env['TO_DATE'] = (day-timedelta(days=1)).strftime("%Y-%m-%d")
else:
    sparkjob_env['FROM_DATE'] = args.from_date
    sparkjob_env['TO_DATE'] = args.to_date
if args.secretpath:
    sparkjob_env['OPENSEARCH_SECRET_PATH'] = args.secretpath
if args.prod:
    sparkjob_env['PROD'] = 'true'


path = pathlib.Path(args.path)
pathpy = path.with_suffix('.py')
cmd = f"jupyter nbconvert --to python {path}"
print(f'Running: {cmd}')
subprocess.run(cmd, shell=True, timeout=3600, check=True)

cmd = f'spark-submit --master yarn --packages org.apache.spark:spark-avro_2.12:3.5.0 {pathpy}'
print(f'Running: {cmd}')
subprocess.run(cmd, shell=True, timeout=3600, check=True, env=sparkjob_env)
