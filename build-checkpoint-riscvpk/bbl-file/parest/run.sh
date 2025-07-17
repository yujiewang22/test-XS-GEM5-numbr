#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/parest
cd /spec
date -R

echo '======== BEGIN parest ========'
./parest ref.prm
echo '======== END   parest ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
