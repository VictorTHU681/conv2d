#!/usr/bin/env python3
"""Validate balanced K5 copy-order screening, including correctness and hashes."""
from pathlib import Path
from statistics import median
from collections import defaultdict
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K5_ORDER_DONE' in s
s=s.split('K5_ORDER_SCREEN_DONE')[0]
assert 'FAIL' not in s
for line in (Path('results/post63/k5-copy-order/sources.sha256').read_text()+Path('results/post63/k5-copy-order/audit_sources.sha256').read_text()).splitlines():
    digest,path=line.split();assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$',s,re.M)
assert s.count('STATE_SWEEP PASS cases=261')==10
assert s.count('PLANAR_GUARD_PASS cases=224')==2
assert len(re.findall(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s))==2
assert re.findall(r'^K5_ORDER_PACK variant=(\w+) mode=(-?\d+)$',s,re.M)==[(v,str(m)) for v in ['early','spread'] for m in [-1,0,1,2,3]]
assert s.count('K5_EXTENDED PASS cases=574')==2
spans=re.findall(r'K5_INPUT_AUDIT calls=(\d+) outside=(\d+)',s)
assert len(spans)==2 and all(int(n)>0 and int(bad)==0 for n,bad in spans)
for kind in ['GUARD','EXTENDED','OWNERSHIP']:
    assert re.findall(r'^K5_ORDER_'+kind+r' variant=(\w+)$',s,re.M)==['early','spread']
for v in ['baseline','early','spread']:
    assert re.search(r'^[0-9a-f]{64}\s+build/post63/k5-copy-order/bench_'+v+r'$',s,re.M)
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
variants=['baseline','early','spread']
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
data={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'K5_ORDER memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
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
print(f'3,058 state/guard cases, 1,148 extended cases, 108 output-ownership cases and {len(data)*5} timed hashes PASS; zero observed active conflicts.')
print('Six permutations, five timings/process. Median process-average GFLOPS, screening only. Three fixed executables: accepted local scalar-unroll baseline ce57939/0136da05, earlier copy load (early), and distributed plane stores (spread). No runtime experiment knob. Ratios use this same-job local baseline; no gains are added from prior v63 comparisons.')
print('\n| Memory | KH | Baseline | Early load | Spread stores | Early/base | Spread/base |')
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
