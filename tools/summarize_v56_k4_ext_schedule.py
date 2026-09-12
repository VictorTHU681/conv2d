#!/usr/bin/env python3
"""Validate real K4 EXT scheduling and NaN-ring controls."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K4_EXT_SCHEDULE_DONE' in s and 'FAIL' not in s
assert s.count('STATE_SWEEP PASS cases=261')==6
assert s.count('PLANAR_GUARD_PASS cases=224')==2
assert len(re.findall(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s))==1
assert re.findall(r'^EXT_SCHEDULE_PACK mode=(-?\d+)$',s,re.M)==['-1','0','1','2','3']
assert s.count('EXT_SCHEDULE_POISON')==1
variants=['baseline','blocked','interleaved']
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
data={};counts=defaultdict(int);order=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'EXT_SCHEDULE memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
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
print(f'Interleaved candidate: 2,014 state/guard cases (including NaN-ring controls), 54 runtime output-ownership cases and {len(data)*5} timed hashes PASS; zero observed active conflicts.')
print('All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8b6b295, not published v55.')
print('\n| Memory | KH | Baseline | Blocked EXT | Interleaved EXT | Blocked/base | Interleaved/base | Interleaved/blocked |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b,c=[median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | '+ ' | '.join(f'{100*(x-1):+.2f}%' for x in [b/a,c/a,c/b])+' |')
