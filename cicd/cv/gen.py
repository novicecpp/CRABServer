import sys
import yaml
import copy
import os

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

versiontmp = os.getenv('CMSSW_VERSIONS', None)
if versiontmp:
    cmsswversions = versiontmp.split(',')
else:
    cmsswversions = [ k for k,_ in cmsswinfo.items() ]

filepath = '.gitlab-ci.yml.tmp'
with open(filepath, 'r') as file:
    gitlabCI = yaml.safe_load(file)

for version in cmsswversions:
    versiondict = cmsswinfo[version]
    executeCV = copy.deepcopy(gitlabCI['.execute_cv'])
    executeCV['variables'].update(versiondict)
    gitlabCI[f'execute_cv_{versiondict["CMSSW_release"]}'] = executeCV
    checkCV = copy.deepcopy(gitlabCI['.check_cv'])
    checkCV['variables'].update(versiondict)
    gitlabCI[f'check_cv_{versiondict["CMSSW_release"]}'] = checkCV

filepath = 'generated-gitlab-ci.yml'
with open(filepath, 'w') as file:
    yaml.dump(gitlabCI, file, sort_keys=False)
