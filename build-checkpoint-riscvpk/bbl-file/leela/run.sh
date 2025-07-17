#!/bin/sh
echo '===== Start running SPEC2017 ====='
echo '======== BEGIN leela ========'
set -x
md5sum /spec/leela
date -R
/spec_common/before_workload
cd /spec && ./leela ref.sgf
/spec_common/trap
date -R
set +x
echo '======== END   leela ========'
echo '===== Finish running SPEC2017 ====='
