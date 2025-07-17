#!/bin/sh
echo '===== Start running SPEC2017 ====='
set -x
md5sum /spec/x264
date -R

/spec_common/before_workload

set +x
echo '======== BEGIN x264_pass1 ========'
set -x
cd /spec && ./x264 --pass 1 --stats x264_stats.log --bitrate 1000 --frames 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720
set +x
echo '======== END   x264_pass1 ========'

echo '======== BEGIN x264_pass2 ========'
set -x
cd /spec && ./x264 --pass 2 --stats x264_stats.log --bitrate 1000 --dumpyuv 200 --frames 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720
set +x
echo '======== END   x264_pass2 ========'

echo '======== BEGIN x264_seek ========'
set -x
cd /spec && ./x264 --seek 500 --dumpyuv 200 --frames 1250 -o BuckBunny_New.264 BuckBunny.yuv 1280x720
set +x
echo '======== END   x264_seek ========'
set -x

/spec_common/trap

date -R
set +x
echo '===== Finish running SPEC2017 ====='
