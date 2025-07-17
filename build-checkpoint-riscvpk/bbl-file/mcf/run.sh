#!/bin/sh
echo '===== Start running SPEC2017 ====='
echo '======== BEGIN mcf ========'
set -x
md5sum /spec/mcf
date -R
/spec_common/before_workload
cd /spec && ./mcf inp.in
/spec_common/trap
date -R
set +x
echo '======== END   mcf ========'
echo '===== Finish running SPEC2017 ====='
