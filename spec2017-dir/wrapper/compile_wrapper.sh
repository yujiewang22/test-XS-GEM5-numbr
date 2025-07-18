#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 核心数
export PARALLEL_NUM=4

# 当前工作目录
export WORKDIR=$(pwd)

# 其他环境
export SPEC=${WORKDIR}/../cpu2017
export SPEC_LITE=${WORKDIR}/CPU2017LiteWrapper

# RISC-V工具链
export PATH=${WORKDIR}/../../software/riscv64gc/bin:$PATH

# 生成目录名
export COLLECT_DIR_NAME=RXU7

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

# 编译
cd ${SPEC}
source shrc

cd ${SPEC_LITE}
make copy_allr

export ARCH=riscv64
export CROSS_COMPILE=riscv64-unknown-linux-gnu-
make build_allr -j${PARALLEL_NUM}

# 收集结果
cd ${SPEC_LITE}
bash scripts/collect.sh ${COLLECT_DIR_NAME}

