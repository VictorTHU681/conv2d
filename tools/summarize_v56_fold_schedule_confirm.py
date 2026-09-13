#!/usr/bin/env python3
"""Validate an independent alternating baseline/F4 weave comparison."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
s=Path(sys.argv[1]).read_text();assert 'FOLD_CONFIRM_DONE' in s and 'FAIL' not in s
for digest in ['ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026',
               '8433e2d4af9f9fb6a35ffd1ebb5e1af27c17207d467f7c381e2ffa7483525135',
               '2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927']:
    assert re.search(r'^'+digest+r'\s+',s,re.M),digest
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM'];data={};order=defaultdict(list);key=None
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
for line in s.splitlines():
    m=re.match(r'FOLD_CONFIRM memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None;kh=int(m[6]);assert tuple(map(int,m.groups()[3:]))==shapes[kh]
        key=m[1],int(m[2]),m[3],kh;order[key[0],key[1],kh].append(key[2])
    m=re.match(r'\s*(\d+)\s*x\s*(\d+)\s+(\d+)\s*x\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m:
        assert key is not None and key not in data and tuple(map(int,m.groups()[:4]))==shapes[key[3]]
        assert m[8]=='PASS' and float(m[7])==0;data[key]=float(m[6]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in memories for r in range(6) for v in ['baseline','f4'] for k in shapes}
for m in memories:
    for k in shapes:
        assert Counter(tuple(order[m,r,k]) for r in range(6))==Counter({('baseline','f4'):3,('f4','baseline'):3})
print(f'{len(data)} original-benchmark full-reference checks PASS, maximum errors zero. Six alternating rounds, five timings per process.')
print('Independent confirmation: accepted local v56 3df5c69 / ebf36923 versus F4 weave 8433e2d4. Median of six process-average GFLOPS. DDR/HBM are separate; no historical percentages are added.')
print('\n| Memory | KH | Accepted baseline | F4 weave | F4 weave/base |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a,b=[median(data[m,r,v,k] for r in range(6)) for v in ['baseline','f4']]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {100*(b/a-1):+.2f}% |')

print('\nObserved within-round ranges are not confidence intervals.')
print('\n| Memory | KH | Median paired change | Paired range | Positive rounds |')
print('| --- | ---: | ---: | --- | ---: |')
for m in memories:
    for k in shapes:
        ratios=[100*(data[m,r,'f4',k]/data[m,r,'baseline',k]-1) for r in range(6)]
        print(f'| {m} | {k} | {median(ratios):+.2f}% | {min(ratios):+.2f}% to {max(ratios):+.2f}% | {sum(x>0 for x in ratios)}/6 |')
