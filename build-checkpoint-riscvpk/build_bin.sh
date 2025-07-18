#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 核心数
export PARALLEL_NUM=16

# 当前工作目录
export WORKDIR=$(pwd)

# 其他环境变量
export RISCV_ROOTFS_HOME=${WORKDIR}/riscv-rootfs
export NOOP_HOME=${WORKDIR}/riscv-pk

# RISC-V工具链
export RISCV=${WORKDIR}/../software/riscv64gc
export PATH=$RISCV/bin:$PATH

# 工作负载
export WORKLOAD_DIR=${WORKDIR}/bbl-file

# SPEC2017
export COLLECT_DIR_NAME=RXU7
export SPEC2017_EXE_DIR=${WORKDIR}/../spec2017-dir/wrapper/CPU2017LiteWrapper/cpu2017_build.${COLLECT_DIR_NAME}
export SPEC2017_INPUT_DIR=${WORKDIR}/../spec2017-dir/cpu2017-compiled/cpu2017/spec2017_run_dir

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

# 配置linux内核，修改initramfs
cd ${WORKDIR}/riscv-linux
make clean
make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- fpga_defconfig
make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- menuconfig

# 打包生成bbl文件
cd ${NOOP_HOME}
make clean
rm -rf build
make -j${PARALLEL_NUM}

# 复制bbl文件
cp ${NOOP_HOME}/build/bbl.bin ${WORKLOAD_DIR}/bbl.bin

