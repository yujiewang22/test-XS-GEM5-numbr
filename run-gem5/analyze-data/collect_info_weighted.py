# -*- coding: utf-8 -*-
import os
import re
import pandas as pd

# 配置：要查找的条目
STAT_ITEMS = [
    "system.cpu.ipc",
    "system.cpu.branchMissPrediction",
    # "system.cpu.mmu.dtb.misses",
    # "system.cpu.mmu.dtb.accesses",
    # "system.cpu.mmu.dtb.l1tlbRemove",
    # "system.cpu.commit.pagefaulttimes",
]

# 相关路径
script_dir = os.path.dirname(os.path.abspath(__file__))
weight_dir = os.path.join(script_dir, "../result-folder/checkpoint_example_result")
input_dir = os.path.join(script_dir, "../result-folder/run-all-checkpoint-result")
output_dir = script_dir

# Benchmark 顺序
benchmark_order = [
    'perlbench', 'gcc', 'mcf', 'omnetpp', 'xalancbmk', 'x264', 'deepsjeng', 'leela',
    'exchange2', 'xz', 'bwaves', 'cactuBSSN', 'namd', 'parest', 'povray', 'lbm', 'wrf',
    'blender', 'cam4', 'imagick', 'nab', 'fotonik3d', 'roms'
]

def load_simpoint_mapping(simpoint_file):
    """
    读取 simpoints0: 返回 {索引号: 切片号}
    """
    mapping = {}
    with open(simpoint_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                slice_id = parts[0]
                index = int(parts[1])
                mapping[index] = slice_id
    return mapping

def load_weights(weight_file):
    """
    读取 weights0: 返回 {索引号: 权重}
    """
    weights = {}
    with open(weight_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                weight_val = float(parts[0])
                index = int(parts[1])
                weights[index] = weight_val
    return weights

def calculate_weighted_stat(benchmark):
    """
    计算某个 benchmark 的加权统计值
    """
    benchmark_path = os.path.join(input_dir, benchmark)
    simpoint_file = os.path.join(weight_dir, benchmark, "cluster", "bbl", "simpoints0")
    weight_file   = os.path.join(weight_dir, benchmark, "cluster", "bbl", "weights0")

    if not os.path.isfile(simpoint_file) or not os.path.isfile(weight_file):
        return {f'Weighted {item}': None for item in STAT_ITEMS}

    sim_mapping = load_simpoint_mapping(simpoint_file)
    weights = load_weights(weight_file)

    weighted_sums = {item: 0.0 for item in STAT_ITEMS}

    print(f"\n{'='*20} Benchmark: {benchmark} {'='*20}")
    
    for index, slice_id in sim_mapping.items():
        weight_val = weights.get(index, 0)

        # 拼接目录名：<benchmark>_<切片号>
        slice_dir = os.path.join(benchmark_path, f"{benchmark}_{slice_id}", "m5out", "stats.txt")
        if not os.path.isfile(slice_dir):
            print(f"  警告: 切片 {slice_id} 的 stats.txt 文件不存在")
            continue

        print(f"[CHECKPOINT] Idx: {slice_id:>10}, Weight: {weight_val:>10.8f}")

        with open(slice_dir, 'r') as f:
            stats_content = f.readlines()

        for item in STAT_ITEMS:
            for line in stats_content:
                if item in line:
                    # 修改正则表达式来匹配小数
                    match = re.search(rf"{re.escape(item)}\s+([\d.]+)", line)
                    if match:
                        value = float(match.group(1))
                        # ==================== 详细的调试信息 ====================
                        print(f"    [INFO] {item:<40} = {value:>10.8f} (Idx: {slice_id:>10}, Weight: {weight_val:>10.8f}, SubValue: {value * weight_val:>10.8f})")
                        # ========================================================
                        weighted_sums[item] += value * weight_val
                    else:
                        print(f"    警告: 在切片 {slice_id} 中未找到 {item} 的数值")
                    break 

    print(f"\n{'='*60}")
    for item in STAT_ITEMS:
        weighted_avg = weighted_sums[item]
        print(f"{item:<40} 加权平均值: {weighted_avg:>10.8f}")
    print(f"{'='*60}")
        
    return {f'Weighted {item}': weighted_sums[item] for item in STAT_ITEMS}

def main():
    benchmark_list = []

    for benchmark in benchmark_order:
        data = {'Benchmark': benchmark}
        stats = calculate_weighted_stat(benchmark)
        data.update(stats)
        benchmark_list.append(data)

    df = pd.DataFrame(benchmark_list)
    df['Benchmark'] = pd.Categorical(df['Benchmark'], categories=benchmark_order, ordered=True)
    df = df.sort_values('Benchmark')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, "collect_info_weighted.csv")
    df.to_csv(output_file, index=False)

    print(f"\n统计条目: {', '.join(STAT_ITEMS)}")
    print(f"结果保存: {output_file}")

if __name__ == "__main__":
    main()
