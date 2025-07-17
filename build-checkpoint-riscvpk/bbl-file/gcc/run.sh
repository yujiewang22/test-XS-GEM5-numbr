#!/bin/sh
echo '===== Start running SPEC2017 ====='
set -x
md5sum /spec/gcc
date -R

/spec_common/before_workload

set +x
echo '======== BEGIN gcc_pp_O2 ========'
set -x
cd /spec && ./gcc gcc-pp.c -O2 -finline-limit=36000 -fpic -o gcc-pp.opts-O2_-finline-limit_36000_-fpic.s
set +x
echo '======== END   gcc_pp_O2 ========'

echo '======== BEGIN gcc_pp_O3 ========'
set -x
cd /spec && ./gcc gcc-pp.c -O3 -finline-limit=0 -fif-conversion -fif-conversion2 -o gcc-pp.opts-O3_-finline-limit_0_-fif-conversion_-fif-conversion2.s
set +x
echo '======== END   gcc_pp_O3 ========'

echo '======== BEGIN gcc_ref32_O3 ========'
set -x
cd /spec && ./gcc ref32.c -O3 -fselective-scheduling -fselective-scheduling2 -o ref32.opts-O3_-fselective-scheduling_-fselective-scheduling2.s
set +x
echo '======== END   gcc_ref32_O3 ========'

echo '======== BEGIN gcc_ref32_O5 ========'
set -x
cd /spec && ./gcc ref32.c -O5 -o ref32.opts-O5.s
set +x
echo '======== END   gcc_ref32_O5 ========'

echo '======== BEGIN gcc_small_O3 ========'
set -x
cd /spec && ./gcc gcc-smaller.c -O3 -fipa-pta -o gcc-smaller.opts-O3_-fipa-pta.s
set +x
echo '======== END   gcc_small_O3 ========'
set -x

/spec_common/trap

date -R
set +x
echo '===== Finish running SPEC2017 ====='
