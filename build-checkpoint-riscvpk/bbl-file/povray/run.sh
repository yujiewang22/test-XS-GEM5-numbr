#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/povray
cd /spec
date -R

echo '======== BEGIN povray ========'
./povray SPEC-benchmark-ref.ini
echo '======== END   povray ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
