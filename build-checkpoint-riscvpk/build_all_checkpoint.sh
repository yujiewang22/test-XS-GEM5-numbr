#!/bin/bash

start_time=$(date +%s)

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 核心数
export PARALLEL_NUM=1

# 当前工作目录
export WORKDIR=$(pwd)

# 负载与间隔配置
export WORKLOAD_DIR=${WORKDIR}/bbl-file
export interval=$((50*1000*1000))

# Checkpoint 格式：gz/zstd
export CHECKPOINT_FORMAT=gz

# 相关软件
export NEMU_HOME=${WORKDIR}/NEMU
export NEMU=${NEMU_HOME}/build/riscv64-nemu-interpreter
export GCPT=${NEMU_HOME}/resource/gcpt_restore/build/gcpt.bin
export SIMPOINT=${NEMU_HOME}/resource/simpoint/simpoint_repo/bin/simpoint

# 输出结果
export CHECKPOINT_RESULT_NAME=checkpoint_example_result
export RESULT=${NEMU_HOME}/${CHECKPOINT_RESULT_NAME}
export profiling_result_name=simpoint-profiling

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

# clean
rm -rf ${RESULT}

# using config: riscv64-xs-cpt_defconfig

# Profiling
profiling(){
    workload=$1
    log=${RESULT}/${workload}/logs/profiling_logs
    mkdir -p $log

    $NEMU ${WORKLOAD_DIR}/${workload}/bbl.bin \
        -D ${RESULT}/${workload} -w bbl -C $profiling_result_name \
        -b --simpoint-profile --cpt-interval ${interval} \
        -r $GCPT \
        > ${log}/bbl-out.txt 2> ${log}/bbl-err.txt
}

# Cluster
cluster(){
    workload=$1
    log=${RESULT}/${workload}/logs/cluster_logs
    mkdir -p $log

    export CLUSTER=${RESULT}/${workload}/cluster/bbl
    mkdir -p $CLUSTER

    random1=`head -20 /dev/urandom | cksum | cut -c 1-6`
    random2=`head -20 /dev/urandom | cksum | cut -c 1-6`

    $SIMPOINT \
        -loadFVFile ${RESULT}/${workload}/${profiling_result_name}/bbl/simpoint_bbv.gz \
        -saveSimpoints $CLUSTER/simpoints0 -saveSimpointWeights $CLUSTER/weights0 \
        -inputVectorsGzipped -maxK 30 -numInitSeeds 2 -iters 1000 -seedkm ${random1} -seedproj ${random2} \
        > ${log}/bbl-out.txt 2> ${log}/bbl-err.txt
}

# Checkpointing
checkpoint(){
    workload=$1
    log=${RESULT}/${workload}/logs/checkpoint_logs
    mkdir -p $log

    export CLUSTER=$RESULT/${workload}/cluster

    $NEMU ${WORKLOAD_DIR}/${workload}/bbl.bin \
         -D ${RESULT}/${workload} -w bbl -C spec-cpt  \
         -b -S $CLUSTER --cpt-interval $interval \
         -r $GCPT \
         --checkpoint-format ${CHECKPOINT_FORMAT} \
         > ${log}/bbl-out.txt 2> ${log}/bbl-err.txt
}

export -f profiling
export -f cluster
export -f checkpoint

workloads=$(find ${WORKLOAD_DIR} -mindepth 1 -maxdepth 1 -type d -printf "%f\n")

# Function to run the steps for a single workload (profiling -> cluster -> checkpoint)
run_workload(){
    workload=$1
    echo "Running profiling, cluster, and checkpoint for workload: ${workload}"
    profiling "${workload}"
    cluster "${workload}"
    checkpoint "${workload}"
}

export -f run_workload

# Use GNU Parallel to run workloads in parallel
# The -j option controls the number of parallel jobs (0 means as many as possible)
parallel -j${PARALLEL_NUM} run_workload ::: ${workloads}

echo "All workloads have been processed."

# -----------------------------------------------------------
# 3、其他输出
# -----------------------------------------------------------

echo "Parallel_num = ${PARALLEL_NUM}"
end_time=$(date +%s)
execution_time=$((end_time - start_time))
hours=$((execution_time / 3600))
minutes=$(( (execution_time % 3600) / 60 ))
seconds=$((execution_time % 60))
echo "Execution time = ${hours} hours, ${minutes} minutes, ${seconds} seconds"
