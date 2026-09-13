#!/usr/bin/env python3
"""Validate guided chunks and balanced screening positions."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'GUIDED_CHUNKS_DONE' in s and 'FAIL' not in s
assert s.count('STATE_SWEEP PASS cases=261')==12
assert s.count('PLANAR_GUARD_PASS cases=224')==2
assert len(re.findall(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s))==2
assert re.findall(r'^GUIDED_PACK variant=(\w+) mode=(-?\d+)$',s,re.M)==[(v,str(m)) for v in ['grow2','grow4'] for m in [-1,0,1,2,3]]
assert re.findall(r'^GUIDED_OVERRIDE variant=(\w+) step=1$',s,re.M)==['grow2','grow4']
assert re.findall(r'^GUIDED_LONG variant=(\w+) mode=(-?\d+)$',s,re.M)==[(v,str(m)) for v in ['grow2','grow4'] for m in [-1,0]]
long_checks=re.findall(r'GUIDED_OVERLAP PASS cases=12 calls=(\d+) large=(\d+) small=(\d+) active_conflicts=0',s)
assert len(long_checks)==4 and all(all(int(x)>0 for x in row) for row in long_checks)
variants=['baseline','grow2','grow4']
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
data={};counts=defaultdict(int);order=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'GUIDED memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None
        kh=int(m[6]);assert (int(m[4]),int(m[5]),int(m[7]))=={39:(4096,6144,39),41:(6144,4096,41),55:(4256,6390,55),81:(6390,4256,81)}[kh]
        key=m[1],int(m[2]),m[3],kh;order[key[0],key[1],key[3]].append(key[2])
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
    m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
    if m:
        assert key is not None and key not in data and counts[key]==5
        data[key]=float(m[1]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in memories for r in range(6) for v in variants for k in [39,41,55,81]}
for m in memories:
    for k in [39,41,55,81]:
        assert {tuple(order[m,r,k]) for r in range(6)}==set(permutations(variants))
print(f'3,580 state/guard cases, 156 runtime output-ownership cases (48 long cases confirm both large and small chunks) and {len(data)*5} timed hashes PASS; zero observed active conflicts.')
print('All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8629457 / 1d3f5071, not published v55.')
print('\n| Memory | KH | Baseline | Grow by two | Grow by four | Grow2/base | Grow4/base |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b,c=[median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | '+ ' | '.join(f'{100*(x/a-1):+.2f}%' for x in [b,c])+' |')
