#!/usr/bin/env python3
"""Validate the capacity repair and direct published-v55 comparison."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
s=Path(sys.argv[1]).read_text();assert 'CAPACITY_CONFIRM_DONE' in s and 'FAIL' not in s
for digest in ['489948afe02f83758a88fc7903be6f06b3ab06b00d6c65e9f189ebd48cc52d61',
               'ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026',
               '2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927']:
    assert re.search(r'^'+digest+r'\s+',s,re.M),digest
assert s.count('PLAN_THREADS PASS cases=24')==2
assert s.count('STATE_SWEEP PASS cases=261')==5
assert s.count('PLANAR_GUARD_PASS cases=224')==1
assert re.findall(r'^CAPACITY_THREAD_POOL (\d+)$',s,re.M)==['0','1']
assert re.findall(r'^CAPACITY_PACK (-?\d+)$',s,re.M)==['-1','0','1','2','3']
print('48 actual shape/thread-switch cases, 1,305 state cases and 224 guards PASS.')
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM'];data={};order=defaultdict(list);key=None
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
for line in s.splitlines():
    m=re.match(r'CAPACITY_CONFIRM memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None;kh=int(m[6]);assert tuple(map(int,m.groups()[3:]))==shapes[kh]
        key=m[1],int(m[2]),m[3],kh;order[key[0],key[1],kh].append(key[2])
    m=re.match(r'\s*(\d+)\s*x\s*(\d+)\s+(\d+)\s*x\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m:
        assert key is not None and key not in data and tuple(map(int,m.groups()[:4]))==shapes[key[3]]
        assert m[8]=='PASS' and float(m[7])==0;data[key]=float(m[6]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in memories for r in range(6) for v in ['v55','capacity'] for k in shapes}
for m in memories:
    for k in shapes:
        assert Counter(tuple(order[m,r,k]) for r in range(6))==Counter({('v55','capacity'):3,('capacity','v55'):3})
print(f'{len(data)} original-benchmark full-reference checks PASS, maximum errors zero. Six alternating rounds, five timings per process.')
print('Direct comparison: published v55 0a39770 / 489948af versus capacity repair ebf36923. Median of six process-average GFLOPS. DDR/HBM are separate; no historical percentages are added.')
print('\n| Memory | KH | Published v55 | Capacity repair | Repair/v55 |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a,b=[median(data[m,r,v,k] for r in range(6)) for v in ['v55','capacity']]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {100*(b/a-1):+.2f}% |')

print('\nObserved within-round ranges are not confidence intervals.')
print('\n| Memory | KH | Median paired change | Paired range | Positive rounds |')
print('| --- | ---: | ---: | --- | ---: |')
for m in memories:
    for k in shapes:
        ratios=[100*(data[m,r,'capacity',k]/data[m,r,'v55',k]-1) for r in range(6)]
        print(f'| {m} | {k} | {median(ratios):+.2f}% | {min(ratios):+.2f}% to {max(ratios):+.2f}% | {sum(x>0 for x in ratios)}/6 |')
