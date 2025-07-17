#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/lbm
cd /spec
date -R

echo '======== BEGIN lbm ========'
./lbm 3000 reference.dat 0 0 100_100_130_ldc.of
echo '======== END   lbm ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
