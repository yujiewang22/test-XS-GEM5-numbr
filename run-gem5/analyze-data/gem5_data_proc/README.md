This is a tool to extract GEM5 & XS performance counter from the output of GEM5 & XS simulation.
# Examples to extract GEM5 & XS performance counter

We use `batch.py` to extract the performance counter for each checkpoint.

Get full option list of `batch.py` with
``` shell
batch.py -h
```

To use `batch.py` anywhere, you can add `gem5_data_proc` to you PATH:
``` shell
export PATH='/path/to/gem5_data_proc':$PATH
```

Use `batch.py` to extract GEM5's cache performance counters:
``` shell
batch.py -s /path/to/results/top/directory  --cache -f stats.txt
```

Include only a specific benchmark like gromacs:
``` shell
batch.py -s /path/to/results/top/directory  --cache -f stats.txt -F gromacs
```

Use `batch.py` to extract XS's cache & branch performance counters:
``` shell
batch.py -s /path/to/results/top/directory --cache --branch --xiangshan -f simulator_err.txt
```
# Example for eval targets

The `eval targets` trick makes use of Python's `eval` to avoid creating new options for every new stat group

Use eval target to extract GEM5's memory bandwidth:
``` shell
batch.py -s /path/to/results/top/directory --eval-stat mem_targets
```

Using eval target to extract GEM5's memory bandwidth and memory dependency counters:

``` shell
batch.py -s /path/to/results/top/directory --eval-stat mem_targets#mem_dep_targets
```

Using eval target to extract XS's memory bandwidth and memory dependency counters:

``` shell
batch.py -s /path/to/results/top/directory -X --eval-stat mem_targets#mem_dep_targets
```

# Compute weighted performance

**Unified weighted metric computation with batch.py**

Now we use `batch.py` to compute the performance for each checkpoint.
Then we use simpoint_cpt/compute_weighted.py to compute **weighted metrics** and **scores**
Example usage here:
``` shell
export PYTHONPATH=`pwd`

example_stats_dir=/nfs-nvme/home/share/zyy/gem5-results/example-outputs

mkdir -p results

python3 batch.py -s $example_stats_dir -t --topdown-raw -o results/example.csv  # The topdown results for each checkpoint

python3 simpoint_cpt/compute_weighted.py \
    -r results/example.csv \
    -j simpoint_cpt/resources/spec06_rv64gcb_o2_20m.json \
    -o results/example-weighted.csv  # The weighted topdown counters for each benchmark

python3 simpoint_cpt/compute_weighted.py \
    -r results/example.csv \
    -j simpoint_cpt/resources/spec06_rv64gcb_o2_20m.json \
    --score results/example-score.csv  # The SPEC score for each benchmark and overll score

```

## Analysis topdown performance

First, we need to get the topdown outputs for one tests
```
bash example-scripts/gem5-topdown-tag.sh spec_ideal_numBr6
```

Then, we can use `topdown/draw_new.py` to analyze the topdown performance, and draw pictures, save to `figure/`
```
python3 topdown/draw_new.py -f=1 -p  -t1=spec_ideal_numBr4 -t2=spec_ideal_numBr6
# -f=1 means the highest level of detail
# -p means print the level 1 percentage and diff two tags outputs
# -t1=spec_ideal_numBr4 means the first tag
# -t2=spec_ideal_numBr6 means the second tag
```

```
python3 topdown/draw_new.py -f=3 -c=Frontend -t1=spec_ideal_numBr4 -t2=spec_ideal_numBr6
# -f=3 means the most detailed level
# -c=Frontend means the category, choises: Frontend, Backend, BadSpec
```

## Dual-core performance
stats parser will obtain XS_CORE_ID from environment variables to choose which core to compute score:

```
export XS_CORE_ID
python3 batch.py -s $example_stats_dir -o results/$tag-core$core.csv -X
```

Full scripts to obtain dual-core performance is in `example-scripts/xs-dual-core.sh`

# How to add more interested stats

## Simple stats target group
See `cache_targets` defined in utils/target_stats.py and its usage in batch.py.

Simple stats target group contains **a list of targets**.
Each entry of the list is a **regex**.
`batch.py` will ``search'' for the pattern in given stats file,
and name it with the first match group in parentheses.
For example
``` regex
(l3\.demandAcc)esses::total'
        ^
        The first match group, used as name
```

## Complex stats target

Complex stats target group is a dictionary.
The key of an entry is the name of the target.
The value of an entry has two possible types: `list` or `str`.

If `str`, it is the regex to search.
(`xs_cache_targets_nanhu` in utils/target_stats.py is an example.)

If `list`, like `xs_cache_targets_22_04_nanhu`,
value[0] is the regex to search, while values[1] is how many times such pattern repeats.
This is to handle the case that one pattern repeats multiple times in specific version of XS.
The occurs because the performance counter of different banks of L2/L3 caches are named the same.
Because this is to handle the buggy behavior in RTL, this type of stats group is rarely used
and is out of maintained.


# Assumed directory structure 
A typical directory structure of GEM5 results looks like:

``` shell
.
|-- bwaves_1299
|   |-- completed
|   |-- dcache_miss.db
|   |-- dramsim3.json
|   |-- dramsim3.txt
|   |-- dramsim3epoch.json
|   |-- log.txt
|   `-- m5out
|       |-- TableHitCnt.txt
|       |-- altuseCnt.txt
|       |-- config.ini
|       |-- config.json
|       |-- misPredIndirect.txt
|       |-- misPredIndirectStream.txt
|       |-- missHistMap.txt
|       |-- stats.txt
|       |-- topMisPredictHist.txt
|       `-- topMisPredicts.txt
`-- gcc_2000
    |-- completed
    |-- dcache_miss.db
    |-- dramsim3.json
    |-- dramsim3.txt
    |-- dramsim3epoch.json
...
```

A typical directory structure of XS looks like:
```
.
|-- GemsFDTD_1041040000000_0.022405
|   |-- simulator_err.txt
|   `-- simulator_out.txt
|-- GemsFDTD_1121140000000_0.004928
|   |-- simulator_err.txt
|   `-- simulator_out.txt
|-- GemsFDTD_1175660000000_0.022268
|   |-- simulator_err.txt
|   `-- simulator_out.txt
...
```

