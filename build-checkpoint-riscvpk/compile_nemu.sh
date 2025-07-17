#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 核心数
export PARALLEL_NUM=16

# 当前工作目录
export WORKDIR=$(pwd)

# NEMU
export NEMU_HOME=${WORKDIR}/NEMU

# RISC-V工具链
export RISCV_TOOL_DIR=${WORKDIR}/../software/riscv64gc

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

# 构建simpoint
cd ${NEMU_HOME}/resource/simpoint/simpoint_repo
make clean
make -j${PARALLEL_NUM}

# 构建nemu
cd ${NEMU_HOME}
make clean
make riscv64-xs-cpt_defconfig
make menuconfig
make -j${PARALLEL_NUM}

# 构建gcpt_restore
cd ${NEMU_HOME}/resource/gcpt_restore
export PATH=${RISCV_TOOL_DIR}/bin:$PATH
make clean
make -j${PARALLEL_NUM}

