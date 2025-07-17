#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/fotonik3d
cd /spec
date -R

echo '======== BEGIN fotonik3d ========'
./fotonik3d 1am0 1122214447 122
echo '======== END   fotonik3d ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
