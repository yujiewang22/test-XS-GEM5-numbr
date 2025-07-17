#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 当前工作目录
export WORKDIR=$(pwd)

# 其他目录
export RUN_RESULT_DIR=${WORKDIR}/run-all-checkpoint-result
export REORG_RUN_RESULT_DIR=${WORKDIR}/reorg-run-all-checkpoint-result

# -----------------------------------------------------------
# 2、执行过程 
# -----------------------------------------------------------

mkdir -p ${REORG_RUN_RESULT_DIR}

for bench_dir in "${RUN_RESULT_DIR}"/*/; do
    for subdir in "$bench_dir"*/; do
        subdir_name=$(basename "$subdir")
        cp -r "$subdir" "${REORG_RUN_RESULT_DIR}/$subdir_name"
    done
done

echo "Finish copy to ${REORG_RUN_RESULT_DIR}"
