#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/cam4
cd /spec
date -R

echo '======== BEGIN cam4 ========'
./cam4
echo '======== END   cam4 ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
