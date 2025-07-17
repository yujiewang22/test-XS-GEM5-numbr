import sys
from os.path import join as pjoin
from os.path import expanduser as expu
import re
import json
from copy import deepcopy
import pandas as pd

from local_configs import Env
from paths import *
from . import target_stats as t
from topdown import topdown_stat_map as tsm

env = Env()

def user_verify():
    ok = input('Is that OK? (y/n)')
    if ok != 'y':
        sys.exit()


def left_is_older(x, y):
    return os.path.getmtime(x) < os.path.getmtime(y)

# reverse a file

def reverse_readline(filename: str, buf_size=8192):
    """a generator that returns the lines of a file in reverse order"""
    with open(filename) as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] != '\n':
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if len(lines[index]):
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment


# scan pairs and filters:

def pair_to_dir(x, y):
    return x + '_' + y

def dir_to_pair(d):
    return d.split('_')

def pairs(stat_dir, return_path=True):
    # type: (string) -> list
    pairs_s = [x for x in os.listdir(expu(stat_dir))]
    pair_dirs = [pjoin(stat_dir, x) for x in pairs_s]
    if return_path:
        # return [x for x in pair_dirs if os.path.isdir(expu(x)) and '_' in x]
        return [x for x in pair_dirs if os.path.isdir(expu(x))]
    else:
        return [x[1] for x in zip(pair_dirs, pairs_s) \
                if os.path.isdir(expu(x[0]))]

def stat_filt(pairs, dirs, stat_name='stats.txt'):
    # type: (list) -> list
    new_pairs = []
    new_paths =[]
    for pair, path in zip(pairs, dirs):
        if os.path.isfile(expu(pjoin(path, stat_name))):
            new_pairs.append(pair)
            new_paths.append(path)
    return new_pairs, new_paths

def pair_to_full_path(path, pairs):
    return [expu(pjoin(path, p)) for p in pairs]

def pair_filt(pairs: list, fname: str):
    with open(fname) as f:
        selected_pairs = f.readlines()
        proc_pairs = []
        for p in selected_pairs:
            p = p.rstrip().replace(' ', '_')
            proc_pairs.append(p)
        new_list = []
        for p in pairs:
            if p in proc_pairs:
                new_list.append(p)
        return new_list


def time_filt(dirs):
    # type: (list) -> list
    def newer_than_gem5(d):
        stat = pjoin(expu(d), 'stats.txt')
        return left_is_older(pjoin(os.environ['gem5_build'], 'gem5.fast'), stat)
    return list(filter(newer_than_gem5, dirs))


def print_list(l):
    cur_line_len = 0
    for x in l:
        if cur_line_len + len(str(x)) > 70:
            print('')
            cur_line_len = 0
        print(x, '\t', end=' ')
        cur_line_len += len(str(x))
    print('')


def print_option(opt):
    cur_line_len = 0
    for line in opt:
        if line.startswith('-') or cur_line_len + len(line) > 80:
            print('')
            cur_line_len = 0
        cur_line_len += len(line)
        print(line, end=' ')
    print('')


def print_2_tuple(x, y):
    x = str(x)
    if isinstance(y, float):
        y = '{:6f}'.format(y)
    else:
        y = str(y)
    print(x.ljust(25), y.rjust(20))

def print_dict(d):
    for k in d:
        print_2_tuple(k, d[k])


def print_line():
    print('---------------------------------------------------------------')


def extract_weight_from_config(config_file: str):
    assert osp.isfile(config_file)
    weight_pattern = re.compile('.*/{\w+}_\d+_(\d+\.\d+([eE][-+]?\d+)?)/.*\.gz')
    with open(config_file) as jf:
        js = json.load(jf)
        gcpt_file = js['system']['gcpt_file']
        m = weight_pattern.match(gcpt_file)
        assert m is not None
        weight = float(m.group(1))
        return weight


def extract_insts_from_config(config_file: str):
    assert osp.isfile(config_file)
    insts_pattern = re.compile(f'.*/_(\d+)_\.gz')
    with open(config_file) as jf:
        js = json.load(jf)
        gcpt_file = js['system']['gcpt_file']
        m = insts_pattern.match(gcpt_file)
        assert m is not None
        insts = int(m.group(1))
        return insts

def extract_insts_from_path(d: str):
    p_dir_insts = re.compile('/(\d+)/.*.txt')
    m = p_dir_insts.search(d)
    assert m is not None
    return int(m.group(1))


# this functions get all stats dumps
def get_all_chunks(stat_file: str, config_file: str, insts_from_dir):
    buff = []
    chunks = {}
    p_insts = re.compile('cpus?.committedInsts\s+(\d+)\s+#')
    if not insts_from_dir:
        insts = extract_insts_from_config(config_file)
    else:
        insts = extract_insts_from_path(stat_file)
    with open(expu(stat_file)) as f:
        for line in f:
            buff.append(line)
            if line.startswith('---------- End Simulation Statistics   ----------'):
                assert(insts)
                chunks[insts] = buff
                buff = []
            elif p_insts.search(line) is not None:
                insts += int(p_insts.search(line).group(1))
                insts = round(insts, -2)
    return chunks


def get_host_seconds(stat_file: str):
    p_host_time = re.compile('hostSeconds\s+(\S+)\s+#.*')
    host_time = 0.0
    with open(expu(stat_file)) as f:
        for line in f:
            m = p_host_time.match(line.strip())
            if m is not None:
                host_time += float(m.group(1))
            else:
                if line.startswith('hostSeconds'):
                    print(line)
                    assert False
    assert host_time > 0.1
    return host_time
    

# this functions get only the last dumps or the nearest stats dump
def get_raw_stats_around(stat_file: str, insts: int=200*(10**6),
                         cycles: int = None)-> list:
    buff = []

    # p_insts = re.compile('(?:cpus?|switch_cpus_1)\.committedInsts\s+(\d+)\s+#')
    # p_cycles = re.compile('(?:cpus?|switch_cpus_1)\.numCycles\s+(\d+)\s+#')

    print(stat_file)
    for line in reverse_readline(expu(stat_file)):
        buff.append(line)

        if line.startswith('---------- Begin Simulation Statistics ----------'):
            return buff

    return []
    # raise Exception("No beginning line found")


def to_num(x: str) -> (int, float):
    if '.' in x:
        return float(x)
    else:
        return int(x)

time_pattern = re.compile('\[PERF \]\[time=\s*(\d+)\].*')
def xs_get_time(line):
    return int(time_pattern.match(line).group(1))


def xs_get_mshr_latency(line: str, lv: str):
    # TOP.SimTop.l_soc.core_with_l2.l2cache.
    
    if lv == 'l2':
        pattern = re.compile(r"\[PERF \]\[time=\s+\d+\] TOP\.SimTop\.l_soc\.core_with_l2\.l2cache\.slices_(?P<bank>\d+)\.mshrCtl: mshr_latency_(?P<mshr_id>\d+)_(?P<lat_low>\d+)_(?P<lat_high>\d+),\s+(?P<count>\d+)")
    elif lv == 'l3':
        pattern = re.compile(r"\[PERF \]\[time=\s+\d+\] TOP\.SimTop\.l_soc\.l3cacheOpt\.slices_(?P<bank>\d+)\.mshrAlloc: mshr_latency_(?P<mshr_id>\d+)_(?P<lat_low>\d+)_(?P<lat_high>\d+),\s+(?P<count>\d+)")
    elif lv == 'l1d':
        pattern = re.compile(r"\[PERF \]\[time=\s+\d+\] TOP\.SimTop\.l_soc\.core_with_l2\.core\.memBlock\.dcache\.dcache\.missQueue\.entries_(?P<mshr_id>\d+): load_miss_penalty_to_use_(?P<lat_low>\d+)_(?P<lat_high>\d+),\s+(?P<count>\d+)")
    else:
        raise Exception("Unhandle cache levl")

    m = pattern.match(line)
    if m is None:
        return False, None, None, None, None
    mshr_id = int(m.group('mshr_id'))
    if 'bank' in m.groupdict(): 
        bank = int(m.group('bank'))
    else:
        bank = 0
    lat_low = int(m.group('lat_low'))
    lat_high = int(m.group('lat_high'))
    count = int(m.group('count'))
    lat_avg = (lat_high + lat_low) / 2.0
    total_latency = lat_avg * count

    if lv == 'l1d':
        print(f'{lv} mshr id: {mshr_id}, {lat_low}-{lat_high}: {total_latency} cycles')
    return True, int(bank), int(mshr_id), f'{lat_low}-{lat_high}', count


def xs_get_stats(stat_file: str, targets: list,
              insts: int=200*(10**6), re_targets=False) -> dict:
    
    target_keys = list(targets.keys())
    num_cores = len(list(filter(lambda x: x.startswith('commitInstr'), target_keys)))

    if not os.path.isfile(expu(stat_file)):
        print(stat_file)
    assert(os.path.isfile(expu(stat_file)))
    with open(stat_file) as f:
        lines = f.read().splitlines()

    if lines is None:
        return None

    patterns = {}
    accumulate_table = {}  # key: pattern, value: (count, [matched values])
    for k, p in targets.items():
        if isinstance(p, str):
            patterns[k] = re.compile(p)
        else:
            patterns[k] = re.compile(p[0])
            accumulate_table[k] = (p[1], [])

    stats = {}
    mshr_latency_l2 = {}
    mshr_latency_l3 = {}
    mshr_latency_l1d = {}
    total_access = 0
    total_match = 0
    keep_last = True
    caches = ['l3']  # caches that need to be manually processed
    for ln, line in enumerate(lines):
        matched_re_pattern = False
        for k in patterns:
            m = patterns[k].match(line)
            if not m is None:
                matched_re_pattern = True
                if k in accumulate_table:
                    accumulate_table[k][1].append(to_num(m.group(1)))
                else:
                    stats[k] = to_num(m.group(1))
                break
        if not matched_re_pattern:
            for lv in caches:
                mshr_latency = eval(f'mshr_latency_{lv}')
                matched, bank, mshr_id, bucket, count = xs_get_mshr_latency(line, lv)
                if matched:
                    total_match += 1
                    mshr_latency[bank] = mshr_latency.get(bank, {})
                    mshr_latency[bank][bucket] = mshr_latency[bank].get(bucket, {})
                    if mshr_id in mshr_latency[bank][bucket] and count != 0:
                        total_access += count
                    if keep_last:
                        mshr_latency[bank][bucket][mshr_id] = count
                    else:
                        if mshr_id not in mshr_latency[bank][bucket]:
                            mshr_latency[bank][bucket][mshr_id] = count
    for k in accumulate_table:
        stats[k] = sum(accumulate_table[k][1][-accumulate_table[k][0]:])
    
    desired_keys = set(patterns.keys())
    obtained_keys = set(stats.keys())
    not_found_keys = desired_keys - obtained_keys
    print("Obtained:", obtained_keys)
    print("Not found:", not_found_keys)
    # assert len(not_found_keys) == 0
    if len(not_found_keys) > 0:
        print(f"warning: in {stat_file} not found the following stats:")
        print(f"missing stats: {not_found_keys}")
        print(f"obtained stats: {obtained_keys}")
        # return None means this stat file is invalid
        return None 

    # print(mshr_latency.keys())
    tdf = None
    for lv in caches:
        bucket_sum = {}
        mshr_latency = eval(f'mshr_latency_{lv}')
        for bank in range(4):
            if bank not in mshr_latency:
                continue
            for bucket in mshr_latency[bank]:
                s = sum(mshr_latency[bank][bucket].values())
                bucket_sum[bucket] = bucket_sum.get(bucket, 0) + s
        check_count = 0
        
        print(bucket_sum)
        if tdf is None:
            tdf = pd.DataFrame.from_dict(bucket_sum, orient='index', columns=[lv])
        else:
            tdf[lv] = pd.DataFrame.from_dict(bucket_sum, orient='index', columns=[lv])

        for k, v in bucket_sum.items():
            check_count += v
        print(f'total access: {total_access}, check count: {check_count}, total match: {total_match}')
    

    for lv in caches:
        # for i in tdf.index[:3]:
        #     tdf.at[i, lv] = 0
        tdf[f'{lv}_cum_sum'] = tdf[lv].cumsum()
        tdf[f'{lv}_cum_pct'] = 100*tdf[f'{lv}_cum_sum']/tdf[lv].sum()
        tdf.drop([f'{lv}_cum_sum'], axis=1, inplace=True)

    print(tdf)
    print(stats)

    if not ('commitInstr' in stats and 'total_cycles' in stats):
        print("Warn: rob_commitInstr or totalCycle not exists")
        stats['ipc'] = 0
    else:
        stats['ipc'] = stats['commitInstr']/stats['total_cycles']
        for c in range(1, num_cores):
            stats[f'ipc{c}'] = stats[f'commitInstr{c}']/stats['total_cycles']
    return stats


def gem5_get_stats(stat_file: str, targets: list,
              insts: int=100*(10**6), re_targets=False,
              all_chunks=False, config_file=None, insts_from_dir=False) -> dict:
    if not os.path.isfile(expu(stat_file)):
        print(stat_file)
    assert(os.path.isfile(expu(stat_file)))

    patterns = {}

    assert re_targets
    for meta, regex in targets.items():
        patterns[meta] = re.compile(regex+'\s+(\d+\.?\d*)\s+')

    if not all_chunks:
        lines = get_raw_stats_around(stat_file, insts)
        stats = {}

        # sim_time = get_host_seconds(stat_file)
        # stats['time'] = sim_time

        for line in lines:
            for k in patterns:
                m = patterns[k].search(line)
                if not m is None:
                    stats[k] = to_num(m.group(1))
        return stats
    else:
        assert config_file is not None
        chunks = get_all_chunks(stat_file, config_file, insts_from_dir)
        chunk_stats = {}
        for insts, chunk in chunks.items():
            chunk_stats[insts] = {}
            assert re_targets
            meta_pattern = re.compile('.*\((\w.+)\).*')

            for line in chunk:
                for k in patterns:
                    m = patterns[k].search(line)
                    if not m is None:
                        chunk_stats[insts][m.group(1)] = to_num(m.group(2))
        return chunk_stats


def get_stats(*args, **kwargs) -> dict:
    return gem5_get_stats(*args, **kwargs)


def get_stats_file_name(d: str):
    assert(os.path.isdir(d))
    results = []
    for f in os.listdir(d):
        if os.path.isfile(pjoin(d, f)) and f.endswith('stats.txt'):
            results.append(f)

    if len(results) > 1:
        print("Multiple stats file found!")
        assert False

    elif len(results) == 1:
        return results[0]

    else:
        return None


def get_stats_from_parent_dir(d: str, selected_benchmarks: [], *args, **kwargs):
    ret = {}
    assert(os.path.isdir(d))
    for sub_d in os.listdir(d):
        if os.path.isdir(pjoin(d, sub_d)):
            if '_' in sub_d:
                bmk = sub_d.split('_')[0]
            else:
                bmk = sub_d
            if selected_benchmarks is not None and bmk not in selected_benchmarks:
                continue

            stat_file = get_stats_file_name(pjoin(d, sub_d))
            if stat_file is not None:
                ret[sub_d] = get_stats(pjoin(d, sub_d, stat_file), *args, **kwargs)
    return ret


def add_st_ipc(hpt: str, d: dict, tid: int) -> None:
    num_insts = int(d['committedInsts'])
    if num_insts == 200*10**6:
        make_st_stat_cache()
        df = pd.read_csv(st_cache, index_col=0)
        d['st_ipc_{}'.format(tid)] = df.loc['ipc'][hpt]
    else:
        t = ['cpu\.(ipc)']
        st_d = get_stats(
            pjoin(st_stat_dir, hpt, 'stats.txt'), t,
            num_insts, re_targets=True
        )

        d['st_ipc_{}'.format(tid)] = st_d['ipc']

def add_ipc_pred(d: dict) -> None:
    real_ipc = float(d['st_ipc_0'])
    pred_ipc = float(d['HPTpredIPC'])
    d['IPC prediction error'] = (pred_ipc - real_ipc) / real_ipc

def add_slot_sanity(d: dict) -> None:
    d['slot sanity'] = \
            (float(d['numMissSlots::0']) + \
             float(d['numWaitSlots::0']) + \
             float(d['numBaseSlots::0'])) / (float(d['numCycles']) * 8)

def add_qos(tid: int, d: dict) -> None:
    solo_ipc = float(d['st_ipc_' + str(tid)])
    smt_ipc = float(d['ipc::' + str(tid)])
    d['QoS_' + str(tid)] = smt_ipc / solo_ipc

def add_overall_qos(hpt: str, lpt: str, d: dict) -> None:
    add_st_ipc(hpt, d, 0)
    add_st_ipc(lpt, d, 1)
    add_qos(0, d)
    add_qos(1, d)

    d['overall QoS'] = d['QoS_0'] + d['QoS_1']

def add_branch_mispred(d: dict) -> None:
    branches = float(d['branches'])
    mispred = float(d.get('branchMispredicts', 0.0))
    ind_mispred = float(d.get('indirectMispred', 0.0))
    d['mispredict rate'] = mispred / branches
    print('Commit instr', d['Insts'], mispred)
    d['total branch MPKI'] = mispred / float(d['Insts']) * 1000
    d['indirect branch MPKI'] = ind_mispred / float(d['Insts']) * 1000
    d['direct branch MPKI'] = d['total branch MPKI'] - d['indirect branch MPKI']
    # d['return MPKI'] = float(d['RASIncorrect']) / float(d['Insts']) * 1000

def add_mem_bw(d: dict) -> None:
    to_mc_total = float(d.get('WritebackDirty', 0)) + float(d.get('ReadResp', 0)) + float(d.get('ReadExResp', 0))
    d['Mem_MB'] = to_mc_total * 64 / 1024 / 1024
    d['BW_MB/s'] = to_mc_total * 64 / float(d['Sec']) / 1024 / 1024

def add_pf_accuracy(d: dict) -> None:
    pht_l2_pf_total = float(d.get('pfUnused_srcs::3', 0)) + float(d.get('pfUseful_srcs::3', 0)) + 1
    d['SMS L2 Useful ratio'] = d.get('pfUseful_srcs::3', 0) / pht_l2_pf_total

def xs_add_pf_accuracy(d: dict) -> None:
    assert 'sms_useful' in d
    pht_l2_pf_total = float(d.get('sms_sent', 1))
    d['SMS L2 Useful ratio'] = d.get('sms_useful', 0) / pht_l2_pf_total

def xs_add_branch_mispred(d: dict) -> None:
    mispred = float(d['BpBWrong']) + float(d['BpJWrong']) + float(d['BpIWrong'])
    branches = float(d['BpInstr'])
    d['mispredict rate'] = mispred / branches
    d['total branch MPKI'] = mispred / float(d['commitInstr']) * 1000
    # d['indirect branch MPKI'] = ind_mispred / float(d['Insts']) * 1000
    # d['direct branch MPKI'] = d['total branch MPKI'] - d['indirect branch MPKI']
    # d['return MPKI'] = float(d['RASIncorrect']) / float(d['Insts']) * 1000

def add_cache_mpki(d: dict) -> None:
    d['l1d.data.miss'] = d['dcache_miss'] - d.get('dcache_miss_pref', 0)
    # d['l1d.overall.MPKI'] = d['dcache_miss'] / d['Insts'] * 1000
    d['l1d.data.MPKI'] = d['l1d.data.miss'] / d['Insts'] * 1000
    # d['l1d.pref.MPKI'] = d.get('dcache_miss_pref', 0) / d['Insts'] * 1000

    d['l2.overall.MPKI'] = d.get('l2_miss', 0.0) / d['Insts'] * 1000
    d['l2.data.miss'] = d.get('l2_miss', 0.0) - d.get('l2_miss_l1d_pref', 0.0)
    d['l2.data.MPKI'] = d['l2.data.miss'] / d['Insts'] * 1000

    
    d['l3.data.acc'] = d.get('l3_acc', 0.0) - d.get('l3_acc_l2_pref', 0.0) - d.get('l3_acc_l1_pref', 0.0)
    d['l3.data.miss'] = d.get('l3_acc', 0.0) \
            - d.get('l3_miss_l2_pref', 0.0) - d.get('l3_miss_l1d_pref', 0.0)

    # d.pop('l2_acc_l1d_pref', None)
    # d.pop('l3_miss_l1d_pref', None)
    # d.pop('l3_acc_l2_pref', None)
    # d.pop('l3_miss_l2_pref', None)

    d['l3.data.MPKI'] = float(d.get('l3.data.miss', 0.0)) / float(d['Insts']) * 1000


def xs_add_cache_mpki(d: dict) -> None:
    # L2/L3
    for lv in ['l2', 'l3']:
        d[f'{lv}.data.miss'] = d[f'{lv}_CPULoadData_Miss'] + d[f'{lv}_CPUStoreData_Miss'] + d[f'{lv}_CPUAtomicData_Miss']
        d[f'{lv}.data.acc'] = d[f'{lv}_CPULoadData_Total'] + d[f'{lv}_CPUStoreData_Total'] + d[f'{lv}_CPUAtomicData_Total']
        d[f'{lv}.pref.miss'] = d[f'{lv}_L1InstPrefetch_Miss'] + d[f'{lv}_L1DataPrefetch_Miss'] + d[f'{lv}_Prefetch2L2BOP_Miss'] + \
            d[f'{lv}_Prefetch2L2SMS_Miss'] + d[f'{lv}_Prefetch2L2Stream_Miss'] + d[f'{lv}_Prefetch2L2Stride_Miss'] + \
            d[f'{lv}_Prefetch2L2TP_Miss'] + d[f'{lv}_Prefetch2L2Unknown_Miss']  + d[f'{lv}_Prefetch2L3Unknown_Miss']
        d[f'{lv}.pref.acc'] = d[f'{lv}_L1InstPrefetch_Total'] + d[f'{lv}_L1DataPrefetch_Total'] + d[f'{lv}_Prefetch2L2BOP_Total'] + \
            d[f'{lv}_Prefetch2L2SMS_Total'] + d[f'{lv}_Prefetch2L2Stream_Total'] + d[f'{lv}_Prefetch2L2Stride_Total'] + \
            d[f'{lv}_Prefetch2L2TP_Total'] + d[f'{lv}_Prefetch2L2Unknown_Total']  + d[f'{lv}_Prefetch2L3Unknown_Total']

        d[f'{lv}.data.MPKI'] = d[f'{lv}.data.miss'] / d['commitInstr'] * 1000
        d[f'{lv}.pref.MPKI'] = d[f'{lv}.pref.miss'] / d['commitInstr'] * 1000

    for lv in ['l3']:
        d[f'{lv}.overall.hit'] = 0
        d[f'{lv}.overall.acc'] = 0
        for bank in range(4):
            d[f'{lv}.overall.hit'] += d[f'{lv}_bank_{bank}_hit']
            d[f'{lv}.overall.acc'] += d[f'{lv}_bank_{bank}_acc']
            d.pop(f'{lv}_bank_{bank}_hit', None)
            d.pop(f'{lv}_bank_{bank}_acc', None)

            # d[f'{lv}.overall.normal'] += d[f'{lv}_bank_{bank}_recv_normal']
            # d[f'{lv}.overall.pref'] += d[f'{lv}_bank_{bank}_recv_pref']


        d[f'{lv}.overall.miss'] = d[f'{lv}.overall.acc'] - d[f'{lv}.overall.hit']
        d[f'{lv}.overall.MPKI'] = d[f'{lv}.overall.miss'] / d['commitInstr'] * 1000

    for lv in ['l2', 'l3']:
        for src in t.xs_mem_acc_sources:
            d.pop(f'{lv}_{src}_Total', None)
            d.pop(f'{lv}_{src}_Miss', None)

    # L1D
    d[f'l1d.miss'] = 0
    d[f'l1d.acc'] = 0
    for load_pipeline in range(2):  # TODO remove hardcode
        d[f'l1d.miss'] += d[f'l1d_{load_pipeline}_miss']
        # d.pop(f'l1d_{load_pipeline}_miss')
        d[f'l1d.acc'] += d[f'l1d_{load_pipeline}_acc']
        d.pop(f'l1d_{load_pipeline}_acc')
    d[f'l1d.MPKI'] = d[f'l1d.miss'] / d['commitInstr'] * 1000

def xs_add_mem_bw(d: dict) -> None:
    d['DRAM read Bytes'] = d['l3_bus_acq'] * 32  # 32 byte for each beat
    d['DRAM write Bytes'] = d['l3_bus_rel'] * 32
    clock_rate = 3e9
    d['DRAM read MBytes/s'] = d['DRAM read Bytes'] / d['total_cycles'] / 1024 / 1024 * clock_rate
    d['DRAM total MBytes/s'] = (d['DRAM read Bytes'] + d['DRAM write Bytes']) / d['total_cycles'] / 1024 / 1024 * clock_rate

topdown_filter = [
    'layer1_frontend_bound',
    'layer1_bad_speculation',
    'layer1_retiring',
    # 'layer2_memory_bound',
    'layer2_core_bound',
    # 'layer3_integet_dq',
    # 'layer3_floatpoint_dq',
    # 'layer3_rob',
    # 'layer3_integet_prf',
    # 'layer3_floatpoint_prf',
    # 'layer3_lsu_ports',
    'layer2_memory_bound-tlb',
    'layer2_memory_bound-non_tlb',
    # 'DTlbStall',
    'ipc',
]

def topdown_post_process(df: pd.DataFrame) -> None:
    print('Merge topdown stats with gem5 coarse-grained stats')
    tsm.rename_with_map(df, tsm.gem5_coarse_rename_map)

def xs_topdown_post_process(df: pd.DataFrame) -> None:
    print('Merge topdown stats with XS coarse-grained stats')
    # tsm.rename_with_map(df, tsm.xs_mem_finegrain_rename_map)
    tsm.rename_with_map(df, tsm.xs_coarse_rename_map)

def add_warmup_mpki(d: dict) -> None:
    d['L2MPKI'] = float(d.get('l2_miss', 0)) / float(d['Insts']) * 1000
    d['L3MPKI'] = float(d.get('l3_miss', 0)) / float(d['Insts']) * 1000
    if 'branchMispredicts' in d:
        mispred = float(d['branchMispredicts'])
    else:
        mispred = 0.0
    d['total branch MPKI'] = mispred / float(d['Insts']) * 1000


def rvv_post_process(d: dict) -> None:
    print(d)
    d['unitStrideLoad'] = d['UnitStrideLoad'] + d['UnitStrideMaskLoad'] + d['WholeRegisterLoad']
    d['unitStrideStore'] = d['UnitStrideStore'] + d['WholeRegisterStore']
    d['otherComplexLoad'] = d['StridedLoad'] + d['IndexedLoad'] + d['UnitStrideFaultOnlyFirstLoad']
    keep_keys = ['unitStrideLoad', 'unitStrideStore',
                 'otherComplexLoad', 'SegUnitStrideLoad', 'SegUnitStrideMaskLoad',
                 'SegStridedLoad', 'SegIndexedLoad', 'segUnitStrideNF=4', 'segUnitStrideNF=6', ]

    for k in list(d.keys()):
        if k in t.rvv_targets and k not in keep_keys:
            d.pop(k, None)

def get_spec2017_int():
    with open(os.path.expanduser(env.data('int.txt'))) as f:
        return [x for x in f.read().split('\n') if len(x) > 1]


def get_spec2017_fp():
    with open(os.path.expanduser(env.data('fp.txt'))) as f:
        return [x for x in f.read().split('\n') if len(x) > 1]


def get_all_spec2017_simpoints():
    benchmarks = get_spec2017_int() + get_spec2017_fp()
    points = []
    for b in benchmarks:
        for i in range(0, 3):
            points.append(f'{b}_{i}')
    return points

def find_stats_file(d: str) -> str:
    assert osp.isdir(d)
    stats = []
    for file in os.listdir(d):
        if file.endswith('stats.txt') and osp.isfile(pjoin(d, file)):
            stats.append(pjoin(d, file))
    assert len(stats) == 1
    return stats[0]

def scale_tick(df: pd.DataFrame):
    for col in df:
        if 'Tick' in col:
            df[col] = df[col] / 500.0
    return df


def get_spec_ref_time(bmk, ver):
    if ver == '06':
        top = "/nfs-nvme/home/share/cpu2006v99/benchspec/CPU2006"
        ref_file = "/nfs-nvme/home/share/cpu2006v99/benchspec/CPU2006/{}/data/ref/reftime"
    else:
        assert ver == '17'
        top = "/home/zyy/research-data/spec2017_20201126/benchspec/CPU"
        ref_file = "/home/zyy/research-data/spec2017_20201126/benchspec/CPU/{}/data/refrate/reftime"

    codename = None
    for d in os.listdir(top):
        if osp.isdir(osp.join(top, d)) and bmk in d and '_s' not in d:
            codename = d
    ref_file = ref_file.format(codename)

    pattern = re.compile(r'\d+')
    print(ref_file)
    assert osp.isfile(ref_file)
    with open(ref_file) as f:
        for line in f:
            m = pattern.search(line)
            if m is not None:
                return float(m.group(0))
    return None

if __name__ == '__main__':
    chunks = get_all_chunks(
            '/home51/zyy/expri_results/shotgun/gem5_shotgun_cont_06/FullWindowO3Config/gcc_200/0/m5out/stats.txt',
            '/home51/zyy/expri_results/shotgun/gem5_shotgun_cont_06/FullWindowO3Config/gcc_200/0/m5out/config.json',
            )
    print(chunks.keys())
