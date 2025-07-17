#!/bin/sh
echo '===== Start running SPEC2017 ====='
echo '======== BEGIN xalancbmk ========'
set -x
md5sum /spec/xalancbmk
date -R
/spec_common/before_workload
cd /spec && ./xalancbmk -v t5.xml xalanc.xsl
/spec_common/trap
date -R
set +x
echo '======== END   xalancbmk ========'
echo '===== Finish running SPEC2017 ====='
