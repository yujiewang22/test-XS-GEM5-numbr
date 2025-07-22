#!/bin/bash

start_time=$(date +%s)

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# make核心数
export PARALLEL_NUM=1
# 当前工作目录
export WORKDIR=$(pwd)

# gem5环境
export gem5_home=${WORKDIR}/GEM5
export gem5=${gem5_home}/build/RISCV/gem5.opt
# 相关软件
export GCBV_REF_SO=${gem5_home}/riscv64-nemu-interpreter-c1469286ca32-so
export GCB_RESTORER=${WORKDIR}/gcpt.bin
export GCBV_RESTORER=${WORKDIR}/gcpt.bin
# checkpoint相关路径
export INPUT_BASE_DIR_NAME=checkpoint_example_result
export CHECKPOINT_BASE_DIR=${WORKDIR}/result-folder/${INPUT_BASE_DIR_NAME}
export OUTPUT_BASE_DIR_NAME=run-all-checkpoint-result
# 其他库
export LD_LIBRARY_PATH=${gem5_home}/ext/dramsim3/DRAMsim3:$LD_LIBRARY_PATH

# 其他配置
export MEM_SIZE=8GB
export CHECKPOINT_FORMAT=gz

# -----------------------------------------------------------
# 2、执行过程 
# -----------------------------------------------------------

# 创建文件夹
cd ${WORKDIR}/result-folder
rm -rf ${OUTPUT_BASE_DIR_NAME}
mkdir -p ${OUTPUT_BASE_DIR_NAME}
cd ${OUTPUT_BASE_DIR_NAME}

# Function to run gem5 for a single checkpoint
run_gem5() {
    local checkpoint=$1
    local checkpoint_dir=$(dirname "${checkpoint}")          
    local testcase_name=$(basename "$(realpath "$checkpoint_dir/../../..")")  
    local dir_name=$(basename "$checkpoint_dir")            
    
    # Define output directory based on testcase_name and dir_name
    local sub_output_dir="${testcase_name}/${testcase_name}_${dir_name}"  

    # Check if the directory already exists, if yes, skip simulation
    if [ -d "$sub_output_dir" ]; then
        echo "Directory $sub_output_dir already exists. Skipping simulation for ${checkpoint}."
        return
    fi

    # Create directory and run the simulation
    mkdir -p "$sub_output_dir"
    cd "$sub_output_dir"

    echo "Starting simulation for $sub_output_dir"
      
    ${gem5} ${gem5_home}/configs/example/xiangshan.py \
      --xiangshan-system --cpu-type=DerivO3CPU --cpu-clock=3GHz \
      --mem-type=DRAMsim3 --mem-size=${MEM_SIZE} \
      --dramsim3-ini=${gem5_home}/ext/dramsim3/xiangshan_configs/xiangshan_DDR4_8Gb_x8_3200_2ch.ini \
      --caches --cacheline_size=64 --l1i_size=64kB --l1i_assoc=8 --l1d_size=64kB --l1d_assoc=8 \
      --l1d-hwp-type=XSCompositePrefetcher --short-stride-thres=0 \
      --l2cache --l2_size=1MB --l2_assoc=8 --l3cache --l3_size=16MB --l3_assoc=16 \
      --l1-to-l2-pf-hint --l2-hwp-type=WorkerPrefetcher --l2-to-l3-pf-hint --l3-hwp-type=WorkerPrefetcher \
      --bp-type=DecoupledBPUWithFTB \
      --disable-sc \
      --enable-difftest \
      --difftest-ref-so ${GCBV_REF_SO} \
      --generic-rv-cpt=${checkpoint} \
      --gcpt-restorer=${GCB_RESTORER} \
      --warmup-insts-no-switch=50000000 --maxinsts=100000000
      
    echo "Finished simulation for $sub_output_dir"
}

export -f run_gem5

# Find and run all checkpoints in parallel
find ${CHECKPOINT_BASE_DIR} -type f -path "*/spec-cpt/bbl/*" -name "*.${CHECKPOINT_FORMAT}" | /usr/bin/parallel -j$PARALLEL_NUM run_gem5

echo "All simulations completed"

# -----------------------------------------------------------
# 3、其他输出 
# -----------------------------------------------------------

echo "Parallel_num = $PARALLEL_NUM"
end_time=$(date +%s)
execution_time=$((end_time - start_time))
hours=$((execution_time / 3600))
minutes=$(( (execution_time % 3600) / 60 ))
seconds=$((execution_time % 60))
echo "Execution time = $hours hours, $minutes minutes, $seconds seconds"
