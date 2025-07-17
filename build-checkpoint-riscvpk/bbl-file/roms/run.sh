#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/roms
cd /spec
date -R

echo '======== BEGIN roms ========'
./roms < ocean_benchmark2.in.x
echo '======== END   roms ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
