#!/usr/bin/env python3
"""Require every independent/dependency-bearing EXT throughput record."""
from pathlib import Path
from statistics import median
import re,sys
s=Path(sys.argv[1]).read_text();assert 'EXT_PROBE_DONE' in s and 'FAIL' not in s
variants=['mix0','mix4','mix8','mix16','window_block','window_interleaved'];data={}
assert len(re.findall(r'^EXT_TIMER_HZ [\d.]+ threads=(?:1|38) iters=1000000$',s,re.M))==2
for m in re.finditer(r'^EXT_BUDGET round=(\d+) variant=(\w+) threads=(\d+) ns_per_four_fmopa_min=([\d.]+) mean=([\d.]+) max=([\d.]+)$',s,re.M):
    k=int(m[1]),m[2],int(m[3]);assert k not in data
    lo,av,hi=map(float,m.groups()[3:]);assert 0<lo<=av+0.000001<=hi+0.000002
    data[k]=av
assert set(data)=={(r,v,t) for r in range(3) for v in variants for t in [1,38]}
print('All 36 timing records complete. Median of three thread-mean measurements; nanoseconds normalized to four FMOPA, using actual CNTFRQ.')
print('Register-only synthetic diagnostic. No memory loads, coefficient packing, output handling or convolution validation; these numbers are not operator speedups.')
print('\n| Variant | 1 thread ns/4 FMOPA | 38 threads ns/4 FMOPA | 38-thread cycles at 1.55 GHz (normalized) |')
print('| --- | ---: | ---: | ---: |')
for v in variants:
    a,b=[median(data[r,v,t] for r in range(3)) for t in [1,38]]
    print(f'| {v} | {a:.6f} | {b:.6f} | {b*1.55:.4f} |')
