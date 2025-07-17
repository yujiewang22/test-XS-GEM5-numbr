#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/namd
cd /spec
date -R

echo '======== BEGIN namd ========'
./namd --input apoa1.input --output apoa1.ref.output --iterations 65 
echo '======== END   namd ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
