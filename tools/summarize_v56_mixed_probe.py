#!/usr/bin/env python3
"""Summarize measured arithmetic budgets without inferring physical port topology."""
from pathlib import Path
from collections import defaultdict
from statistics import median
import re,sys
s=Path(sys.argv[1]).read_text();assert 'MIXED_PROBE_DONE' in s
data=defaultdict(list)
for line in s.splitlines():
    m=re.match(r'MIXED_THROUGHPUT round=(\d+) variant=(\w+) threads=(\d+) ns_per_step_min=([\d.]+) mean=([\d.]+) max=([\d.]+)',line)
    if m:
        lo,avg,hi=map(float,m.group(4,5,6));assert lo<=avg<=hi
        data[int(m[3]),m[2]].append((int(m[1]),avg))
variants=['mix'+str(n) for n in [0,2,4,6,8,10,12,16,18]]+['vec'+str(n) for n in [2,4,8,16,18]]
assert set(data)=={(n,v) for n in [1,38] for v in variants}
assert all({r for r,_ in x}=={0,1,2} and len(x)==3 for x in data.values())
print('84 arithmetic diagnostic records; not convolution correctness or benchmark results.')
print('Each mixed step has four FMOPA instructions plus N FMLA instructions on independent accumulators.')
print('Values are medians of three thread-mean timings; cycles use the explicit 1.55 GHz normalization.')
print('\n| Variant | One thread ns/step | One thread normalized cycles | 38 threads ns/step | 38 threads normalized cycles |')
print('| --- | ---: | ---: | ---: | ---: |')
for v in variants:
    a,b=[median(t for _,t in data[n,v]) for n in [1,38]]
    print(f'| {v} | {a:.6f} | {a*1.55:.4f} | {b:.6f} | {b*1.55:.4f} |')
