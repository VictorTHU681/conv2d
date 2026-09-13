#!/usr/bin/env python3
"""Audit identical executable controls; reported differences are not optimization gains."""
from pathlib import Path
from statistics import median
from collections import defaultdict
from itertools import permutations
import re,sys

full=Path(sys.argv[1]).read_text()
assert 'IDENTICAL_DONE' in full and 'PMU_PROBE_END' in full
s=full.split('IDENTICAL_DONE')[0]
assert 'FAIL' not in s
h,source=Path('results/post63/identical-binary/source_binary.sha256').read_text().split()
assert re.search(r'^'+h+r'\s+'+re.escape(source)+r'$',s,re.M)
variants=['0','1','2']
meta={}
for v in variants:
    assert re.search(r'^'+h+r'\s+build/post63/identical-binary/control'+v+r'/bench$',s,re.M)
    m=re.search(r'^CONTROL_INODE variant='+v+r' device=(\d+) inode=(\d+) size=(\d+)$',s,re.M);assert m
    meta[v]=tuple(map(int,m.groups()))
assert meta['0']==meta['1'] and meta['0'][:2]!=meta['2'][:2] and meta['0'][2]==meta['2'][2]
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
shapes={39:(4096,6144,39,39),41:(6144,4096,41,41),55:(4256,6390,55,55),81:(6390,4256,81,81)}
data={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.fullmatch(r'IDENTICAL memory=(\w+) round=(\d+) variant=(\d) shape=(\d+) (\d+) (\d+) (\d+)',line)
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
print(f'{len(data)*5} timed hashes PASS. All three executable hashes equal the validated local baseline; control0/control1 share an inode and control2 has a distinct inode with identical bytes.')
print('Six permutations, five timings/process; ratios of median process-average GFLOPS. Same-length executable paths. Every reported difference is a negative-control observation, not a code improvement or a universal noise bound.')
print('\n| Memory | KH | Control0 | Same-inode control1 | Copy control2 | Control1/0 | Control2/0 |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a,b,c=[median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {100*(b/a-1):+.2f}% | {100*(c/a-1):+.2f}% |')
print('\nAll paired outliers retained; ranges are not confidence intervals.')
for m in memories:
    for k in shapes:
        for v in variants[1:]:
            xs=[100*(data[m,r,v,k]/data[m,r,'0',k]-1) for r in range(6)]
            print(f'{m} KH{k} control{v}: paired median {median(xs):+.2f}%, range {min(xs):+.2f}..{max(xs):+.2f}%, positive {sum(x>0 for x in xs)}/6')
probe=full.split('PMU_PROBE_BEGIN')[1].split('PMU_PROBE_END')[0]
statuses=re.findall(r'^PMU_PROBE_(?:AVAILABLE|UNAVAILABLE status=\d+|NO_PERF)$',probe,re.M)
assert len(statuses)==1
print('\nAllocated-node PMU permission probe: '+statuses[0]+'. A successful true command would only establish access, not useful kernel counters.')
