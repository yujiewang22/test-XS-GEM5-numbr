#!/bin/sh
echo '===== Start running SPEC2017 ====='
set -x
md5sum /spec/xz
date -R

/spec_common/before_workload

set +x
echo '======== BEGIN xz_cld ========'
set -x
cd /spec && ./xz cld.tar.xz 160 19cf30ae51eddcbefda78dd06014b4b96281456e078ca7c13e1c0c9e6aaea8dff3efb4ad6b0456697718cede6bd5454852652806a657bb56e07d61128434b474 59796407 61004416 6
set +x
echo '======== END   xz_cld ========'

echo '======== BEGIN xz_combined ========'
set -x
cd /spec && ./xz input.combined.xz 250 a841f68f38572a49d86226b7ff5baeb31bd19dc637a922a972b2e6d1257a890f6a544ecab967c313e370478c74f760eb229d4eef8a8d2836d233d3e9dd1430bf 40401484 41217675 7
set +x
echo '======== END   xz_combined ========'

echo '======== BEGIN xz_cpu2006 ========'
set -x
cd /spec && ./xz cpu2006docs.tar.xz 250 055ce243071129412e9dd0b3b69a21654033a9b723d874b2015c774fac1553d9713be561ca86f74e4f16f22e664fc17a79f30caa5ad2c04fbc447549c2810fae 23047774 23513385 6e
set +x
echo '======== END   xz_cpu2006 ========'
set -x

/spec_common/trap

date -R
set +x
echo '===== Finish running SPEC2017 ====='
