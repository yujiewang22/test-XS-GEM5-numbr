#!/bin/sh
echo '===== Start running SPEC2017 ====='
set -x
md5sum /spec/perlbench
date -R

/spec_common/before_workload

set +x
echo '======== BEGIN perlbench_diff ========'
set -x
cd /spec && ./perlbench -I./lib diffmail.pl 4 800 10 17 19 300
set +x
echo '======== END   perlbench_diff ========'

echo '======== BEGIN perlbench_spam ========'
set -x
cd /spec && ./perlbench -I./lib checkspam.pl 2500 5 25 11 150 1 1 1 1
set +x
echo '======== END   perlbench_spam ========'

echo '======== BEGIN perlbench_split ========'
set -x
cd /spec && ./perlbench -I./lib splitmail.pl 6400 12 26 16 100 0
set +x
echo '======== END   perlbench_split ========'
set -x

/spec_common/trap

date -R
set +x
echo '===== Finish running SPEC2017 ====='
