#!/usr/bin/env python3
"""Compare whole-process counters and steady diagnostic latency, not official scores."""
from pathlib import Path
from collections import defaultdict
from statistics import median
import re,sys
s=Path(sys.argv[1]).read_text();assert 'K33_WINDOW_PMU_DONE' in s
data=defaultdict(dict);key=None
events=['cycles:u','instructions:u','L1-dcache-loads','L1-dcache-load-misses']
for line in s.splitlines():
    m=re.match(r'K33_PMU memory=(\w+) round=(\d+) variant=(\w+)',line)
    if m:key=m[1],int(m[2]),m[3];assert key not in data
    m=re.search(r'STEADY_DIAGNOSTIC kh=41 runs=200 mean_ms=([\d.]+)',line)
    if m:data[key]['ms']=float(m[1])
    a=line.split(',')
    if len(a)>4 and a[2] in events:
        assert float(a[4])>=99.9 and a[2] not in data[key]
        data[key][a[2]]=float(a[0])
variants=['baseline','outline','unroll4','ext4','tbl4','tbl8']
assert set(data)=={(m,r,v) for m in ['DDR','HBM'] for r in [1,2] for v in variants}
assert all(set(v)==set(events+['ms']) for v in data.values())
print('All 24 diagnostic runs completed, 200 steady calls each; four counters have >=99.9% scheduling coverage.')
print('Counters include initialization, warmup and pool spinning. Percentages compare against outline; negative latency is faster.')
print('\n| Memory | Variant | Mean latency ms (median of two) | Latency change | Instructions | L1 loads | L1 load misses |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: |')
for mem in ['DDR','HBM']:
    for v in variants:
        vals={e:median(data[mem,r,v][e] for r in [1,2]) for e in events+['ms']}
        base={e:median(data[mem,r,'outline'][e] for r in [1,2]) for e in vals}
        changes=[100*(vals[e]/base[e]-1) for e in ['ms','instructions:u','L1-dcache-loads','L1-dcache-load-misses']]
        print(f'| {mem} | {v} | {vals["ms"]:.4f} | '+' | '.join(f'{x:+.2f}%' for x in changes)+' |')
