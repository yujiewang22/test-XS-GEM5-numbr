#!/bin/sh
echo '===== Start running SPEC2017 ====='
echo '======== BEGIN deepsjeng ========'
set -x
md5sum /spec/deepsjeng
date -R
/spec_common/before_workload
cd /spec && ./deepsjeng ref.txt
/spec_common/trap
date -R
set +x
echo '======== END   deepsjeng ========'
echo '===== Finish running SPEC2017 ====='
