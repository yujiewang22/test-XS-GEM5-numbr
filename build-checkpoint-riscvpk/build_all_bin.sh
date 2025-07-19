#!/bin/bash

set -e

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 核心数
export PARALLEL_NUM=16

# 当前工作目录
export WORKDIR=$(pwd)

# 其他环境变量
export RISCV_ROOTFS_HOME=${WORKDIR}/riscv-rootfs
export ROOTFS_IMAGE_DIR=${RISCV_ROOTFS_HOME}/rootfsimg
export NOOP_HOME=${WORKDIR}/riscv-pk

# RISC-V工具链
export RISCV=${WORKDIR}/../software/riscv64gc
export PATH=${RISCV}/bin:$PATH

# 工作负载
export WORKLOAD_DIR=${WORKDIR}/bbl-file

# SPEC2017
export COLLECT_DIR_NAME=RXU6
export SPEC2017_EXE_DIR=${WORKDIR}/../spec2017-dir/wrapper/CPU2017LiteWrapper/cpu2017_build.${COLLECT_DIR_NAME}
export SPEC2017_INPUT_DIR=${WORKDIR}/../spec2017-dir/cpu2017-compiled/cpu2017/spec2017_run_dir

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

BACKUP_DIR=${ROOTFS_IMAGE_DIR}/backup
mkdir -p ${BACKUP_DIR}

INITTAB_BAK=${BACKUP_DIR}/inittab-spec.bak
RUNSH_BAK=${BACKUP_DIR}/run.sh.bak

if [ ! -f "${INITTAB_BAK}" ] || [ ! -f "${RUNSH_BAK}" ]; then
    cp ${ROOTFS_IMAGE_DIR}/inittab-spec ${INITTAB_BAK}
    cp ${ROOTFS_IMAGE_DIR}/run.sh       ${RUNSH_BAK}
fi

build_benchmark() {
    local BENCHMARK_NAME=$1
    local BENCHMARK_PATH=${WORKLOAD_DIR}/${BENCHMARK_NAME}

    echo "[INFO] Starting build for benchmark: ${BENCHMARK_NAME}"

    cp -r ${BENCHMARK_PATH}/* ${ROOTFS_IMAGE_DIR}/

    # 编译Linux内核
    cd ${WORKDIR}/riscv-linux
    make clean
    make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- fpga_defconfig
    # 判断是否为首次构建（即 .config 不存在）
    if [ ! -f ".config" ]; then
        echo "[INFO] .config not found. Launching menuconfig for initial setup..."
        make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- menuconfig
    else
        make -j${PARALLEL_NUM} ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu-
    fi

    # 构建bbl
    cd ${NOOP_HOME}
    make clean
    rm -rf build
    make -j${PARALLEL_NUM}

    cp ${NOOP_HOME}/build/bbl.bin ${BENCHMARK_PATH}/bbl.bin

    cp ${INITTAB_BAK} ${ROOTFS_IMAGE_DIR}/inittab-spec
    cp ${RUNSH_BAK}   ${ROOTFS_IMAGE_DIR}/run.sh

    echo "[SUCCESS] Successfully built benchmark: ${BENCHMARK_NAME}"
}

for dir in ${WORKLOAD_DIR}/*; do
    if [ -d "${dir}" ]; then
        benchmark=$(basename "${dir}")
        build_benchmark "${benchmark}"
    fi
done

