#!/bin/sh
set -x
/spec_common/before_workload
echo '===== Start running SPEC2017 ====='
md5sum /spec/bwaves
cd /spec
date -R

echo '======== BEGIN bwaves_1.in ========'
./bwaves bwaves_1 < ./bwaves_1.in
echo '======== END   bwaves_1.in ========'

date -R

echo '======== BEGIN bwaves_2.in ========'
./bwaves bwaves_2 < ./bwaves_2.in
echo '======== END   bwaves_2.in ========'

date -R

echo '======== BEGIN bwaves_3.in ========'
./bwaves bwaves_3 < ./bwaves_3.in
echo '======== END   bwaves_3.in ========'

date -R

echo '======== BEGIN bwaves_4.in ========'
./bwaves bwaves_4 < ./bwaves_4.in
echo '======== END   bwaves_4.in ========'

date -R

echo '===== Finish running SPEC2017 ====='
/spec_common/trap
