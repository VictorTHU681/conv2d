#!/usr/bin/env python3
"""Summarize complete steady-allocation PMU controls without overstating their scope."""
from pathlib import Path
from statistics import median
from itertools import permutations
from collections import defaultdict
import re,sys
s=Path(sys.argv[1]).read_text();assert 'K5_CHUNK_THREAD_DONE' in s and 'FAIL' not in s
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
values={};events=defaultdict(dict);order=defaultdict(list);key=None
names=['cycles','instructions','L1-dcache-loads','L1-dcache-load-misses']
for line in s.splitlines():
    m=re.match(r'CHUNK_PMU memory=(\w+) round=(\d+) step=(\d+) shape=6144 4096 41 41 runs=200$',line)
    if m:key=m[1],int(m[2]),int(m[3]);order[key[:2]].append(key[2])
    m=re.match(r'STEADY_DIAGNOSTIC kh=41 runs=200 mean_ms=([\d.]+) sample=(\S+)',line)
    if m:
        assert key is not None and key not in values
        assert abs(float(m[2])+2.88966)<1e-5
        values[key]=float(m[1])
    fields=line.split(',')
    if key is not None and len(fields)>4 and fields[2].removesuffix(':u') in names:
        name=fields[2].removesuffix(':u');assert name not in events[key]
        assert float(fields[4])>=99.0,(key,name,fields[4])
        events[key][name]=int(fields[0]);assert events[key][name]>0
expected={(m,r,v) for m in memories for r in range(6) for v in [8,2,4]}
assert set(values)==set(events)==expected
assert all(set(v)==set(names) for v in events.values())
for m in memories: assert {tuple(order[m,r]) for r in range(6)}==set(permutations([8,2,4]))
print(f'{len(values)} steady-allocation PMU processes, 200 timed calls each; all four events >=99% running. Six balanced process permutations.')
print('Counters span the entire process, including allocation, two initial calls and spinning. This is not the official allocation/timing protocol or a complete correctness check.')
print('Median of six processes. Counter totals below are billions of events per process, not exact events per timed call.')
print('\n| Memory | Step | Steady mean ms | Time change vs 8 | Cycles G | Instructions G | L1 loads G | L1 misses G | Miss change vs 8 |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    base=median(values[m,r,8] for r in range(6));bm=median(events[m,r,8][names[-1]] for r in range(6))
    for v in [8,2,4]:
        ms=median(values[m,r,v] for r in range(6));counts=[median(events[m,r,v][n] for r in range(6)) for n in names]
        print(f'| {m} | {v} | {ms:.4f} | {100*(ms/base-1):+.2f}% | '+' | '.join(f'{n/1e9:.4f}' for n in counts)+f' | {100*(counts[-1]/bm-1):+.2f}% |')
