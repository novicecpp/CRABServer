#! /bin/bash
set -euo pipefail
cmsswversions="CMSSW_13_0_2,CMSSW_13_0_2,CMSSW_10_6_26,CMSSW_7_6_7"
cmsswversions="CMSSW_13_0_2"
timenow=$(printf '%(%Y%m%d_%H%M%S)T\n' -1)
echo $timenow > timeline
git add timeline
git commit -m "trigger ci $timenow"
git push gitlab $(git branch --show-current) -o ci.variable="CMSSW_VERSIONS=$cmsswversions" -o ci.variable="Client_Validation_Suite=t"
