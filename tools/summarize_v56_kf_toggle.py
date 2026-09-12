#!/usr/bin/env python3
"""Validate the same-executable table-sharing toggle screen."""
from pathlib import Path
from statistics import median
from collections import defaultdict
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'KF_TOGGLE_DONE' in s and 'FAIL' not in s
assert s.count('STATE_SWEEP PASS cases=261')==2
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
data={};counts=defaultdict(int);order=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'TOGGLE memory=(\w+) round=(\d+) enabled=([01]) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None
        kh=int(m[6]);assert (int(m[4]),int(m[5]),int(m[7]))=={39:(4096,6144,39),55:(4256,6390,55),81:(6390,4256,81)}[kh]
        key=m[1],int(m[2]),int(m[3]),kh;order[key[0],key[1],key[3]].append(key[2])
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
    m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
    if m:
        assert key is not None and key not in data and counts[key]==5
        data[key]=float(m[1]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in memories for r in range(6) for v in [0,1] for k in [39,55,81]}
for (_,r,_),values in order.items(): assert values==([0,1] if r%2==0 else [1,0])
print(f'522 state cases and {len(data)*5} timed output hashes PASS. Same executable; six alternating rounds, five timings per process.')
print('Screening only. Median of six process-average GFLOPS. Environment read and control branch exist in both modes.')
print('\n| Memory | KH | Sharing off | Sharing on | Change |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,55,81]:
        a,b=[median(data[m,r,v,k] for r in range(6)) for v in [0,1]]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {100*(b/a-1):+.2f}% |')
