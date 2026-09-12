#!/usr/bin/env python3
"""Validate an independent alternating baseline/cut2 comparison."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
s=Path(sys.argv[1]).read_text();assert 'CUTOFF_CONFIRM_DONE' in s and 'FAIL' not in s
for digest in ['1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a',
               '41d1a3a4eddaaa3e972a59dcce2b6770d8aa8556850f3558bdd90fe3c16440b2',
               '2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927']:
    assert re.search(r'^'+digest+r'\s+',s,re.M),digest
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM'];data={};order=defaultdict(list);key=None
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
for line in s.splitlines():
    m=re.match(r'CUTOFF_CONFIRM memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None;kh=int(m[6]);assert tuple(map(int,m.groups()[3:]))==shapes[kh]
        key=m[1],int(m[2]),m[3],kh;order[key[0],key[1],kh].append(key[2])
    m=re.match(r'\s*(\d+)\s*x\s*(\d+)\s+(\d+)\s*x\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m:
        assert key is not None and key not in data and tuple(map(int,m.groups()[:4]))==shapes[key[3]]
        assert m[8]=='PASS' and float(m[7])==0;data[key]=float(m[6]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in memories for r in range(6) for v in ['baseline','cut2'] for k in shapes}
for m in memories:
    for k in shapes:
        assert Counter(tuple(order[m,r,k]) for r in range(6))==Counter({('baseline','cut2'):3,('cut2','baseline'):3})
print(f'{len(data)} original-benchmark full-reference checks PASS, maximum errors zero. Six alternating rounds, five timings per process.')
print('Independent confirmation: accepted local v56 8629457 / 1d3f5071 versus global cutoff 41d1a3a4. Median of six process-average GFLOPS. DDR/HBM are separate; no historical percentages are added.')
print('\n| Memory | KH | Accepted baseline | Cutoff 2*threads | Cutoff 2*threads/base |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a,b=[median(data[m,r,v,k] for r in range(6)) for v in ['baseline','cut2']]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {100*(b/a-1):+.2f}% |')

print('\nObserved within-round ranges are not confidence intervals.')
print('\n| Memory | KH | Median paired change | Paired range | Positive rounds |')
print('| --- | ---: | ---: | --- | ---: |')
for m in memories:
    for k in shapes:
        ratios=[100*(data[m,r,'cut2',k]/data[m,r,'baseline',k]-1) for r in range(6)]
        print(f'| {m} | {k} | {median(ratios):+.2f}% | {min(ratios):+.2f}% to {max(ratios):+.2f}% | {sum(x>0 for x in ratios)}/6 |')
