#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/blender
cd /spec
date -R

echo '======== BEGIN blender ========'
./blender sh3_no_char.blend --render-output sh3_no_char_ --threads 1 -b -F RAWTGA -s 849 -e 849 -a
echo '======== END   blender ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
