#!/bin/sh
echo '===== Start running SPEC2017 ====='
echo '======== BEGIN exchange2 ========'
set -x
md5sum /spec/exchange2
date -R
/spec_common/before_workload
cd /spec && ./exchange2 6
/spec_common/trap
date -R
set +x
echo '======== END   exchange2 ========'
echo '===== Finish running SPEC2017 ====='
