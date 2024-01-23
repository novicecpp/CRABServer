#! /usr/bin/env python3
# Parsing wmcore_requirements.txt's format (same format that can use in `pip install -r requirements.txt`).
# Output print repo url and version, separate by space.
# For example:
#   wmcore @ git+https://github.com/dmwm/WMCore@2.2.4rc6
# Output:
#

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename', default='wmcore_requirements.txt')
args = parser.parse_args()
with open(args.filename, encoding='utf-8') as r:
    wmcoreRequirementStr = r.readlines()[0]
_, tmpRepo, tmpCommit = wmcoreRequirementStr.split('@')
commit = tmpCommit.strip()
repo = tmpRepo.split('+')[1].strip()
print(repo, commit)
