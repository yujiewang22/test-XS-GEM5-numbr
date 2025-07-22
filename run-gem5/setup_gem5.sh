#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 当前工作目录
export WORKDIR=$(pwd)

# GEM5 repo
export XS_GEM5_REPO_URL="https://github.com/OpenXiangShan/GEM5.git" 
export GIT_COMMIT_HASH="c9bd2b3a38a1e776df6094bb9f5f6c7879b5e71c"     
export NEMU_DIFFTEST_URL="https://github.com/OpenXiangShan/GEM5/releases/download/2024-10-16/riscv64-nemu-interpreter-c1469286ca32-so"

# gem5_home
export gem5_home=${WORKDIR}/GEM5
                                    
# -----------------------------------------------------------
# 2、执行过程 
# -----------------------------------------------------------

# 克隆仓库并checkout
if [ ! -d "${gem5_home}" ]; then
    git clone ${XS_GEM5_REPO_URL} 
    cd ${gem5_home}
    git checkout ${GIT_COMMIT_HASH}
    wget ${NEMU_DIFFTEST_URL}
fi

