#!/usr/bin/env python3
"""Validate balanced K4 scalar tail screening, state/guard checks and hashes."""
from pathlib import Path
from statistics import median
from collections import defaultdict
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K4_WRITEBACK_DONE' in s
assert 'FAIL' not in s
for line in (Path('results/post64/k4-writeback/sources.sha256').read_text()).splitlines():
    digest,path=line.split();assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$',s,re.M)
assert s.count('STATE_SWEEP PASS cases=261')==10
assert s.count('PLANAR_GUARD_PASS cases=224')==2
assert re.findall(r'^K4_WRITEBACK_PACK variant=(\w+) mode=(-?\d+)$',s,re.M)==[(v,str(m)) for v in ['post','pre'] for m in [-1,0,1,2,3]]
for kind in ['GUARD']:
    assert re.findall(r'^K4_WRITEBACK_'+kind+r' variant=(\w+)$',s,re.M)==['post','pre']
for v in ['baseline','post','pre']:
    assert re.search(r'^[0-9a-f]{64}\s+build/post64/k4-writeback/bench_'+v+r'$',s,re.M)
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
variants=['baseline','post','pre']
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
data={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'K4_WRITEBACK memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None;kh=int(m[6]);assert tuple(map(int,m.groups()[3:]))==shapes[kh]
        key=m[1],int(m[2]),m[3],kh;orders[key[0],key[1],kh].append(key[2])
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
    m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
    if m:
        assert key is not None and key not in data and counts[key]==5
        data[key]=float(m[1]);key=None
assert key is None and set(data)=={(m,r,v,k) for m in memories for r in range(6) for v in variants for k in shapes}
for m in memories:
    for k in shapes:assert {tuple(orders[m,r,k]) for r in range(6)}==set(permutations(variants))
print(f'3,058 state/guard cases and {len(data)*5} timed hashes PASS.')
print('Six permutations, five timings/process. Median process-average GFLOPS, screening only. Baseline is the GPR-loop candidate 490cd8d9 derived from upstream 138dcac, NOT upstream itself. Candidates fold cursor updates into post-index or pre-index loads. Ratios are direct within this job; no historical gains added.')
print('\n| Memory | KH | Baseline | Post-index | Pre-index | Post-index/base | Pre-index/base |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a,b,c=[median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {100*(b/a-1):+.2f}% | {100*(c/a-1):+.2f}% |')
print('\nObserved paired ranges retain all outliers and are not confidence intervals.')
for m in memories:
    for k in shapes:
        for v in variants[1:]:
            xs=[100*(data[m,r,v,k]/data[m,r,'baseline',k]-1) for r in range(6)]
            print(f'{m} KH{k} {v}: paired median {median(xs):+.2f}%, range {min(xs):+.2f}..{max(xs):+.2f}%, positive {sum(x>0 for x in xs)}/6')
