#!/usr/bin/env python3
"""Validate balanced screening of the incoming F4 gate's short-loop alignment."""
from pathlib import Path
from statistics import median
from itertools import permutations
from collections import defaultdict
import re,sys

s=Path(sys.argv[1]).read_text()
assert 'UPSTREAM_SHORTALIGN_DONE' in s and 'FAIL' not in s
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
variants=['baseline','merged','short128'];data={};order=defaultdict(list);counts=defaultdict(int);key=None
for line in s.splitlines():
    m=re.match(r'MEASURE memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)',line)
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
    for k in [39,41,55,81]: assert {tuple(order[m,r,k]) for r in range(6)}==set(permutations(variants))
print(f'{len(data)*5} timed output hashes PASS. All six process permutations per shape/memory; screening, not official acceptance.')
print('Median of six process-average GFLOPS values, five timings per process.')
if len(memories)==1: print('HBM unavailable and skipped; no HBM result.')
print('\n| Memory | KH | Baseline | Merged | Short128 | Merged vs baseline | Short128 vs merged |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b,c=[median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {100*(b/a-1):+.2f}% | {100*(c/b-1):+.2f}% |')
