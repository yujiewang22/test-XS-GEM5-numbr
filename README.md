项目基于开源的XS-GEM5模型，在全系统仿真的基础上，通过采用SimPoint checkpoint机制和多进程加速了运行过程，从而能够快速测算XS-GEM5在不同numBr配置下的SPEC2017分数。

## 一、目录结构

```
test-XS-GEM5-numbr
│
├── software
│   ├── riscv64gc/         # 需自行放置
│   └── riscv-gem5/        # 需自行放置
├──spec2017-dir
│   ├── cpu2017/           # 需自行放置
│   ├── cpu2017-compiled
│   │   ├── rv64g.cfg
│   │   ├── compile_cpu2017.sh
│   │   └── get_spec2017_input.py
│   └── wrapper
│       ├── compile_wrapper.sh
│       └── recompile_wrf.sh
├── build-checkpoint-riscvpk
│   ├── NEMU/
│   ├── bbl-file/
│   ├── riscv-pk/
│   ├── riscv-linux/
│   ├── riscv-rootfs/
│   ├── build_all_bin.sh
│   ├── compile_nemu.sh
│   └── build_all_checkpoint.sh
├── run-gem5
│   ├── GEM5/
│   ├── result-folder
│   │   └── reorg.sh
│   ├── gcpt.bin           # 需后期复制
│   ├── compile_gem5.sh
│   ├── run_all_checkpoint.sh
│   └── analyze-data
│       ├── gem5_data_proc/
│       ├── spec2017_workload_list.txt
│       ├── gen_checkpoint_json.sh
│       └── compute_score.sh
│
└── README.md
```

## 二、版本号

| 名称 | Git 提交哈希 |
| ---------------------- | ------------------------------------------ |
| **CPU2017LiteWrapper** | `763781c73ec9fe818f031e3d300b66fc33eecd7e` |
| **riscv-pk**           | `a621e1620a1ab050d81f53743253e8eb5cf1b24e` |
| **riscv-linux**        | `655055af981b490cb6a12353a5bb846d2be79c6f` |
| **riscv-rootfs**       | `7b6cf0ccdfdb103d2e5918712036634d4e973552` |
| **NEMU**               | `732e4ccdda9f3f5111cd5701a6eca8d887dfb025` |
| **GEM5**               | `c9bd2b3a38a1e776df6094bb9f5f6c7879b5e71c` |
| **gem5_data_proc**     | `d39e49dc591c8ff2d4c6874c9727c8343d8ecb32` |

## 三、构建流程

### 1 构建SPEC2017

#### 1.1 放置工具链

1. 将riscv-gem5工具链置于software目录下

2. 将rv64gc工具链置于software目录下

#### 1.2 放置cpu2017源码

将cpu2017源码置于spec2017-dir目录下

#### 1.3 编译cpu2017

```shell
cd spec2017-dir/cpu2017-compiled
./compile_cpu2017.sh
```

#### 1.4 收集编译后输入文件

```shell
cd spec2017-dir/cpu2017-compiled
python3 get_spec2017_input.py
```

注意x264和fotonik3d测例各有一个输入文件需要使用SPEC2017内部脚本单独构建，此处提供构建好的输入文件，使用时需将各自输入文件放置在前述的输入文件目录中

#### 1.5 编译CPU2017LiteWrapper

1. 编译cpu2017可执行文件

```shell
cd spec2017-dir/wrapper
./compile_wrapper.sh
```

2. 重新单独编译wrf测例

```shell
cd spec2017-dir/wrapper
./recompile_wrf.sh
```

### 2 构建bbl.bin

```shell
cd build-checkpoint-riscvpk
./build_all_bin.sh
```

在bbl-file目录下，完成所有23个benchmark的bbl.bin构建

### 3 构建checkpoint

#### 3.1 编译NEMU

```shell
cd build-checkpoint-riscvpk
./compile_nemu.sh
```

#### 3.2 构建所有checkpoint

```shell
cd build-checkpoint-riscvpk
./build_all_checkpoint.sh
```

在build-checkpoint-riscvpk/NEMU/checkpoint_example_result目录下会生成所有23个benchmark的checkpoint

### 4 GEM5运行checkpoint

#### 4.1 修改numBr配置

修改GEM5/src/cpu/pred/BranchPredictor.py内的numBr参数（1、2、4、8）

#### 4.2 编译GEM5

```shell
cd run-gem5
./compile_gem5.sh
```

GEM5的编译过程可能存在与仓库相关的依赖，这里删去了原有仓库的.git信息使得修改后的GEM5编译时可能会出现blob库问题；因此若编译失败，则需重新clone GEM5源码，并参照提供的文件手动修改

#### 4.3 放置相关文件

1. 下载nemu-so

```shell
cd run-gem5/GEM5
wget https://github.com/OpenXiangShan/GEM5/releases/download/2024-10-16/riscv64-nemu-interpreter-c1469286ca32-so
```

2. 复制gcpt.bin文件

复制build-checkpoint-riscvpk/NEMU/resource/gcpt_restore/build/gcpt.bin文件到run_gem5/gcpt.bin，用于GEM5执行时恢复程序的插入

3. 放置checkpoint文件

将制作好的build-checkpoint-riscvpk/NEMU/checkpoint_example_result目录移动到run-gem5/result-folder内

#### 4.4 运行所有checkpoint

```shell
cd run-gem5
./run_all_checkpoint.sh
```

### 5 计算分数

#### 5.1 整理结果文件

```shell
cd run-gem5/result-folder
./reorg.sh
```

####  5.2 生成json文件

```shell
cd run-gem5/analyze-data
./gen_checkpoint_json.sh
```

#### 5.3 输出分数

```shell
cd run-gem5/analyze-data
./compute_score.sh
```
