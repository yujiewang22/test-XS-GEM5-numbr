#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 核心数
export PARALLEL_NUM=8

# 当前工作目录
export WORKDIR=$(pwd)

# 其他环境
export SPEC=${WORKDIR}/../cpu2017
export SPEC_LITE=${WORKDIR}/CPU2017LiteWrapper

# RISC-V工具链
export PATH=${WORKDIR}/../../software/riscv64gc/bin:$PATH
export RISCV_GEM5_GFORTRAN_PATH=${WORKDIR}/../../software/riscv-gem5/bin/riscv64-unknown-linux-gnu-gfortran

# 生成目录名
export COLLECT_DIR_NAME=RXU7

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

# 编译选项修改
sed -i '1s/^/# /; 2s/^/# /; 3s/^/# /; 4{
    s/^/# /
    a\
SPECFPRATE=521.wrf_r
}
1i# wyj
' "${SPEC_LITE}/Makefile"

sed -i '93i\
# wyj\nSPEC_LDFLAGS += -static
' "${SPEC_LITE}/Makefile.apps"

sed -i '49{
    i# wyj
    s/^/# /
    a\
FC = ${RISCV_GEM5_GFORTRAN_PATH}
}' "${SPEC_LITE}/Makefile.apps"

sed -i 's/-fallow-argument-mismatch/-Wno-argument-mismatch/g' "${SPEC_LITE}/Makefile.apps"
sed -i 's/-fallow-invalid-boz//g' "${SPEC_LITE}/521.wrf_r/Makefile"

# 编译
cd ${SPEC_LITE}/521.wrf_r
rm -rf build

cd ${SPEC}
source shrc
export ARCH=riscv64
export CROSS_COMPILE=riscv64-unknown-linux-gnu-
cd ${SPEC_LITE}
make build_allr -j${PARALLEL_NUM}

# 收集结果
cd ${SPEC_LITE}
cp 521.wrf_r/build/521.wrf_r cpu2017_build.${COLLECT_DIR_NAME}/wrf

