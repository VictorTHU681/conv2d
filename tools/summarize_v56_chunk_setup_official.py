#!/usr/bin/env python3
"""Require the original-reference three-way K5 comparison in all six orders."""
from pathlib import Path
from statistics import median
from itertools import permutations
from collections import defaultdict
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'CHUNK_SETUP_OFFICIAL_DONE' in s and 'FAIL' not in s
variants=['baseline','phase','carry4']
data={};order=defaultdict(list);key=None
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
for line in s.splitlines():
    m=re.match(r'OFFICIAL memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None
        kh=int(m[6]);assert (int(m[4]),int(m[5]),int(m[7]))=={39:(4096,6144,39),41:(6144,4096,41),55:(4256,6390,55),81:(6390,4256,81)}[kh]
        key=m[1],int(m[2]),m[3],kh;order[key[0],key[1],key[3]].append(key[2])
    m=re.match(r'\s*\d+\s*x\s*\d+\s+\d+\s*x\s*\d+\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m and key:
        assert key not in data and m[4]=='PASS' and float(m[3])==0
        data[key]=float(m[2]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in memories for r in range(6) for v in variants for k in [39,41,55,81]}
for m in memories:
    for k in [39,41,55,81]: assert {tuple(order[m,r,k]) for r in range(6)}==set(permutations(variants))
print(f'{len(data)} official full-reference checks PASS, all maximum errors zero. Six permutations; five timings per process.')
print('Median of six process-average GFLOPS. Baseline is accepted local v56 8b6b295, not published v55.')
print('\n| Memory | KH | Baseline | Phase setup | ZA carry4 | Phase/base | Carry/base |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b,c=[median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {100*(b/a-1):+.2f}% | {100*(c/a-1):+.2f}% |')
