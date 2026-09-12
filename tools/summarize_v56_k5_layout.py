#!/usr/bin/env python3
"""Require complete matched outlining controls and balanced process positions."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K5_LAYOUT_DONE' in s and 'FAIL' not in s
assert s.count('STATE_SWEEP PASS cases=261')==4
variants=['baseline','triplet','baseline_out','triplet_out']
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
data={};counts=defaultdict(int);order=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'LAYOUT memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
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
assert set(data)=={(m,r,v,k) for m in memories for r in range(4) for v in variants for k in [39,41,55,81]}
for m in memories:
    for k in [39,41,55,81]:
        rows=[order[m,r,k] for r in range(4)]
        assert all(set(row)==set(variants) for row in rows)
        assert all({row[p] for row in rows}==set(variants) for p in range(4))
        pairs=Counter((row[p],row[p+1]) for row in rows for p in range(3))
        assert pairs==Counter({(a,b):1 for a in variants for b in variants if a!=b})
print(f'1,044 state cases and {len(data)*5} timed output hashes PASS. Four Williams-design rounds balance positions and immediate predecessors.')
print('Screen only; median process-average GFLOPS, five timings per process. K5 is rebased on accepted F4 gate 4817eff.')
print('\n| Memory | KH | Baseline | K5 | Baseline outlined | K5 outlined | K5/base | K5 out/base out | Base out/base | K5 out/base |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b,c,d=[median(data[m,r,v,k] for r in range(4)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {d:.1f} | {100*(b/a-1):+.2f}% | {100*(d/c-1):+.2f}% | {100*(c/a-1):+.2f}% | {100*(d/a-1):+.2f}% |')
