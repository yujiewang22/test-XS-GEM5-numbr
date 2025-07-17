#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/imagick
cd /spec
date -R

echo '======== BEGIN imagick ========'
./imagick -limit disk 0 refrate_input.tga -edge 41 -resample 181% -emboss 31 -colorspace YUV -mean-shift 19x19+15% -resize 30% refrate_output.tga
echo '======== END   imagick ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
