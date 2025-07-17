#!/usr/bin/env python3

from utils import common as c, target_stats as t
import sys
import numpy as np
import pandas as pd

assert len(sys.argv) == 3

experiment = sys.argv[1]
baseline = sys.argv[2]

experiment = c.get_stats_from_parent_dir(experiment, t.flow_target, re_targets=True)
baseline = c.get_stats_from_parent_dir(baseline, t.flow_target, re_targets=True)

def extract(d: dict):
    ret = {}
    for k, v in d.items():
        ret[k] = v.get('WKFlow', 1)
    return ret

experiment = extract(experiment)
baseline = extract(baseline)

df = pd.DataFrame([experiment, baseline])

relative = df.iloc[0]/df.iloc[1]
relative = relative.fillna(1)

ideal = []
for n in relative:
    if n > 1.0:
        ideal.append(n)
    else:
        ideal.append(1.0)

# relative = ideal
print(relative)

mean = [np.mean(relative), 1]
geomean = [np.array(relative).prod() ** (1/len(relative)), 1]
df['mean'] = mean
df['geomean'] = geomean
print(df)

# plt.bar(np.arange(len(df.columns)) - 0.3, df.iloc[0].values, width=0.3 )
# plt.bar(np.arange(len(df.columns)), df.iloc[1].values, width=0.3)
# plt.xticks(np.arange(len(df.columns)), df.columns, rotation=90)
# 
# plt.show()
