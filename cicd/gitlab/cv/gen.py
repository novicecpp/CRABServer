import sys
import yaml
import copy
import os
import argparse


# https://stackoverflow.com/questions/10551117/setting-options-from-environment-variables-when-using-argparse
class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if envvar and envvar in os.environ:
            default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

cmsswinfo = {
    'CMSSW_13_0_2': {'CMSSW_release': 'CMSSW_13_0_2', 'SCRAM_ARCH': 'el8_amd64_gcc11', 'singularity': '8'},
    'CMSSW_12_6_4': {'CMSSW_release': 'CMSSW_12_6_4', 'SCRAM_ARCH': 'el8_amd64_gcc10', 'singularity': '8'},
    'CMSSW_12_5_0': {'CMSSW_release': 'CMSSW_12_5_0', 'SCRAM_ARCH': 'el8_amd64_gcc10', 'singularity': '8'},
    'CMSSW_11_3_4': {'CMSSW_release': 'CMSSW_11_3_4', 'SCRAM_ARCH': 'slc7_amd64_gcc900', 'singularity': '7'},
    'CMSSW_10_6_26': {'CMSSW_release': 'CMSSW_10_6_26', 'SCRAM_ARCH': 'slc7_amd64_gcc700', 'singularity': '7'},
    'CMSSW_10_1_0': {'CMSSW_release': 'CMSSW_10_1_0', 'SCRAM_ARCH': 'slc7_amd64_gcc630', 'singularity': '7'},
    'CMSSW_9_4_21': {'CMSSW_release': 'CMSSW_9_4_21', 'SCRAM_ARCH': 'slc7_amd64_gcc630', 'singularity': '7'},
    'CMSSW_8_0_36': {'CMSSW_release': 'CMSSW_8_0_36', 'SCRAM_ARCH': 'slc7_amd64_gcc530', 'singularity': '7'},
    'CMSSW_7_6_7': {'CMSSW_release': 'CMSSW_7_6_7', 'SCRAM_ARCH': 'slc6_amd64_gcc493', 'singularity': '6'},
    'CMSSW_7_1_29': {'CMSSW_release': 'CMSSW_7_1_29', 'SCRAM_ARCH': 'slc6_amd64_gcc481', 'singularity': '6'},
}

parser = argparse.ArgumentParser(
                    prog='gen.py',
                    description='What the program does',
                    epilog='Text at the bottom of help')
parser.add_argument('filepath')
parser.add_argument('--cmsswversions', action=EnvDefault, envvar='CMSSW_VERSIONS', default=",".join(cmsswinfo.keys()))
args = parser.parse_args()

cmsswversions = args.cmsswversions.split(',')

with open(args.filepath, 'r', encoding='utf-8') as file:
    gitlabCI = yaml.safe_load(file)

copyOfGitlabCI = copy.deepcopy(gitlabCI)
for version in cmsswversions:
    versiondict = cmsswinfo[version]
    checkCV = copy.deepcopy(copyOfGitlabCI['.check_cv'])
    checkCV['variables'].update(versiondict)
    copyOfGitlabCI[f'check_cv_{version}'] = checkCV
    executeCV = copy.deepcopy(copyOfGitlabCI['.execute_cv'])
    executeCV['variables'].update(versiondict)
    copyOfGitlabCI[f'execute_cv_{version}'] = executeCV
outputpath = f'generated-gitlab-ci.yml'
with open(outputpath, 'w', encoding='utf-8') as file:
    yaml.dump(copyOfGitlabCI, file, sort_keys=False)
