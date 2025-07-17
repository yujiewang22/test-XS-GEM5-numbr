#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/wrf
cd /spec
date -R

echo '======== BEGIN wrf ========'
./wrf
echo '======== END   wrf ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
