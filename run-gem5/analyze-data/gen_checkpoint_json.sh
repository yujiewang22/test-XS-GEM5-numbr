#!/bin/bash

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 当前工作目录（上一层目录）
export WORKDIR=$(pwd)/..

# 输入目录
export INPUTDIR=${WORKDIR}/result-folder

# 其他环境目录
export GEM5_DATA_PROC_HOME=${WORKDIR}/analyze-data/gem5_data_proc
export PATH=${GEM5_DATA_PROC_HOME}:$PATH
export PYTHONPATH=${GEM5_DATA_PROC_HOME}:$PYTHONPATH
export GEN_DETAILED_JSON_PATH=${GEM5_DATA_PROC_HOME}/simpoint_cpt/gen_detailed_json.py

# 文件格式
export CHECKPOINT_FORMAT=gz

# -----------------------------------------------------------
# 2、执行过程 
# -----------------------------------------------------------

cd ${GEM5_DATA_PROC_HOME}

python3 ${GEN_DETAILED_JSON_PATH} \
  --from-cpt-name \
  -w ${WORKDIR}/analyze-data/spec2017_workload_list.txt \
  --log-pattern ${INPUTDIR}/checkpoint_example_result/{}/logs/profiling_logs/bbl-out.txt \
  --cpt-pattern="_(\d+)_(.+)_\.${CHECKPOINT_FORMAT}" \
  --cpt-path-pattern ${INPUTDIR}/checkpoint_example_result/{}/spec-cpt/bbl/*/*.${CHECKPOINT_FORMAT} \
  -c spec2017

input_json=${GEM5_DATA_PROC_HOME}/simpoint_cpt/resources/spec2017.json
temp_json=${GEM5_DATA_PROC_HOME}/simpoint_cpt/resources/spec2017_temp.json

jq 'walk(
    if type == "object" and has("insts") then 
        .insts |= (if type == "string" then gsub(","; "") | tonumber else . end)
    else .
    end
)' "${input_json}" > "${temp_json}" && mv "${temp_json}" "${input_json}"

mv ${GEM5_DATA_PROC_HOME}/simpoint_cpt/resources/spec2017.json ${WORKDIR}/analyze-data/spec2017.json
