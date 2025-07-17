#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 当前工作目录（上一级目录）
export WORKDIR=$(pwd)/..
# 其他环境目录
export GEM5_DATA_PROC_HOME=${WORKDIR}/analyze-data/gem5_data_proc
export PATH=/${GEM5_DATA_PROC_HOME}:$PATH
export PYTHONPATH=${GEM5_DATA_PROC_HOME}

# 输入目录
export STAT_DIR=${WORKDIR}/result-folder/reorg-run-all-checkpoint-result
# 输出目录
export RESULT_PATH=${WORKDIR}/analyze-data/results

# -----------------------------------------------------------
# 2、执行过程 
# -----------------------------------------------------------

rm -rf ${RESULT_PATH}
mkdir -p ${RESULT_PATH}

python3 ${GEM5_DATA_PROC_HOME}/batch.py -s ${STAT_DIR} -t --topdown-raw -o ${RESULT_PATH}/example.csv

python3 ${GEM5_DATA_PROC_HOME}/simpoint_cpt/compute_weighted.py \
    -r ${RESULT_PATH}/example.csv \
    -j ${WORKDIR}/analyze-data/spec2017.json \
    --spec-version 17 \
    --score ${RESULT_PATH}/example-score.csv
