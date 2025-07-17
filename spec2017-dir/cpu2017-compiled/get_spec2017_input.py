import os
import shutil

# -----------------------------------------------------------
# 1、配置环境 
# -----------------------------------------------------------

# 定义源目录和目标根目录
base_dir = os.path.dirname(os.path.abspath(__file__))
source_root = os.path.join(base_dir, "cpu2017/benchspec/CPU")
target_root = os.path.join(base_dir, "cpu2017/spec2017_run_dir")
completion_marker = ".copy_complete" 

# -----------------------------------------------------------
# 2、构建过程 
# -----------------------------------------------------------

def get_max_name_length():
    max_length = 0
    if os.path.exists(source_root):
        for entry in os.listdir(source_root):
            if entry.endswith("_r") and os.path.isdir(os.path.join(source_root, entry)):
                max_length = max(max_length, len(entry))
    return max_length

def process_directory(benchmark_dir, max_name_length):
    benchmark_name = os.path.basename(benchmark_dir)
    if not benchmark_name.endswith("_r"):
        return
    
    target_name = benchmark_name.split(".")[1].replace("_r", "")
    target_dir = os.path.join(target_root, target_name)
    marker_file = os.path.join(target_dir, completion_marker)

    padded_name = benchmark_name.ljust(max_name_length)

    if os.path.exists(marker_file):
        print(f"{padded_name}  已经完成复制，跳过")
        return True

    data_path = os.path.join(benchmark_dir, "data")
    if not os.path.exists(data_path):
        return
    
    copied_files = []
    for subdir in ["all", "refrate"]:
        input_path = os.path.join(data_path, subdir, "input")
        if os.path.exists(input_path):
            for root, _, files in os.walk(input_path):
                rel_path = os.path.relpath(root, input_path)  
                dest_path = os.path.join(target_dir, rel_path)
                
                os.makedirs(dest_path, exist_ok=True)  
                
                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_path, file)
                    try:
                        shutil.copy2(src_file, dest_file)
                        copied_files.append(dest_file)
                    except Exception as e:
                        print(f"复制失败: {src_file} -> {dest_file}, 错误: {e}")
                        return False
    
    if copied_files:
        with open(marker_file, "w") as f:
            f.write("Copy completed.\n")
        print(f"{padded_name}  处理完成，共复制 {len(copied_files)} 个文件")
        return True
    else:
        print(f"{padded_name}  没有找到可复制的文件")
        return False

def main():
    if not os.path.exists(source_root):
        print("源目录不存在:", source_root)
        return

    max_name_length = get_max_name_length()  # 获取最长的 benchmark 名称长度

    success = True
    for entry in os.listdir(source_root):
        benchmark_path = os.path.join(source_root, entry)
        if os.path.isdir(benchmark_path):
            result = process_directory(benchmark_path, max_name_length)
            if result is False:
                success = False

    if success:
        print("所有文件成功复制")
    else:
        print("部分文件复制失败，请检查错误信息")

if __name__ == "__main__":
    main()

