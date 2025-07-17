#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/nab
cd /spec
date -R

echo '======== BEGIN nab ========'
./nab 1am0 1122214447 122
echo '======== END   nab ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
