#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/cactuBSSN
cd /spec
date -R

echo '======== BEGIN cactuBSSN ========'
./cactuBSSN spec_ref.par
echo '======== END   cactuBSSN ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
