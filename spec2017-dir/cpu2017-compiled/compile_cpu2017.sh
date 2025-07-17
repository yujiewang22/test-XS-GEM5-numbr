#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 当前工作目录
export WORKDIR=$(pwd)

# 其他环境
export CPU2017_DIR=${WORKDIR}/..
export RISCV_GEM5_DIR=${WORKDIR}/../../software/riscv-gem5

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

# 复制cpu2017源码
cd ${WORKDIR}
cp -r ${CPU2017_DIR}/cpu2017 ./cpu2017
export spec17root=${WORKDIR}/cpu2017

# 复制配置文件
cp rv64g.cfg ${spec17root}/config

# 编译源码a
cd ${spec17root}
source shrc
runcpu -config=rv64g -action build all tune=base

