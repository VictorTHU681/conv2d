#!/usr/bin/env python3
"""Validate balanced K5 prefix-layout screening, including correctness and hashes."""
from pathlib import Path
from statistics import median
from collections import defaultdict
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K5_COPY_DONE' in s
s=s.split('K5_COPY_SCREEN_DONE')[0]
assert 'FAIL' not in s
for line in (Path('results/post61/k5-copy-layout/sources.sha256').read_text()+Path('results/post61/k5-copy-layout/audit_sources.sha256').read_text()).splitlines():
    digest,path=line.split();assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$',s,re.M)
assert s.count('STATE_SWEEP PASS cases=261')==15
assert s.count('PLANAR_GUARD_PASS cases=224')==3
assert len(re.findall(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s))==3
assert re.findall(r'^K5_COPY_PACK variant=(\w+) mode=(-?\d+)$',s,re.M)==[(v,str(m)) for v in ['baseline','exact','triples'] for m in [-1,0,1,2,3]]
assert s.count('K5_EXTENDED PASS cases=574')==3
spans=re.findall(r'K5_INPUT_AUDIT calls=(\d+) outside=(\d+)',s)
assert len(spans)==3 and all(int(n)>0 and int(bad)==0 for n,bad in spans)
for kind in ['GUARD','EXTENDED','OWNERSHIP']:
    assert re.findall(r'^K5_COPY_'+kind+r' variant=(\w+)$',s,re.M)==['baseline','exact','triples']
assert re.search(r'^[0-9a-f]{64}\s+build/post61/k5-copy-layout/bench$',s,re.M)
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
variants=['baseline','exact','triples']
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
data={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'K5_COPY memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
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
print(f'4,587 state/guard cases, 1,722 extended cases, 162 output-ownership cases and {len(data)*5} timed hashes PASS; zero observed active conflicts.')
print('Six permutations, five timings/process. Median process-average GFLOPS, screening only. One executable derived from v61 b3140af; baseline selects the original alignment policy. Runtime control overhead is shared. This is not an unchanged-v61 binary.')
print('\n| Memory | KH | Baseline | Zero prefix | Triples prefix | Exact/base | Triples/base |')
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
