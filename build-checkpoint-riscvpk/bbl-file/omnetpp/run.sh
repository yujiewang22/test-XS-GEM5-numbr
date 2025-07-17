#!/bin/sh
echo '===== Start running SPEC2017 ====='
echo '======== BEGIN omnetpp ========'
set -x
md5sum /spec/omnetpp
date -R
/spec_common/before_workload
cd /spec && ./omnetpp -c General -r 0
/spec_common/trap
date -R
set +x
echo '======== END   omnetpp ========'
echo '===== Finish running SPEC2017 ====='
