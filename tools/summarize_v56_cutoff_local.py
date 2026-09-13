#!/usr/bin/env python3
"""Validate local-first cutoff and balanced screening positions."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'CUTOFF_LOCAL_DONE' in s and 'FAIL' not in s
for digest in ['1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a',
               '41d1a3a4eddaaa3e972a59dcce2b6770d8aa8556850f3558bdd90fe3c16440b2',
               'e0b363e28e20c04cf6e8a52f115088190f7e6d31fbe86a5807576e1f11785b19',
               'e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad']:
    assert re.search(r'^'+digest+r'\s+',s,re.M),digest
assert s.count('STATE_SWEEP PASS cases=261')==6
assert s.count('PLANAR_GUARD_PASS cases=224')==1
assert len(re.findall(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s))==1
assert re.findall(r'^LOCAL_PACK variant=(\w+) mode=(-?\d+)$',s,re.M)==[(v,str(m)) for v in ['local'] for m in [-1,0,1,2,3]]
assert re.findall(r'^LOCAL_OVERRIDE variant=(\w+) step=1$',s,re.M)==['local']
assert re.findall(r'^LOCAL_LONG variant=(\w+) mode=(-?\d+)$',s,re.M)==[(v,str(m)) for v in ['local'] for m in [-1,0]]
long_checks=re.findall(r'GUIDED_OVERLAP PASS cases=12 calls=(\d+) large=(\d+) small=(\d+) active_conflicts=0',s)
assert len(long_checks)==2 and all(all(int(x)>0 for x in row) for row in long_checks)
variants=['baseline','cutoff','local']
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
data={};counts=defaultdict(int);order=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'LOCAL memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
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
    for k in [39,41,55,81]:
        assert {tuple(order[m,r,k]) for r in range(6)}==set(permutations(variants))
print(f'1,790 state/guard cases, 78 runtime output-ownership cases (24 long cases confirm both large and small chunks) and {len(data)*5} timed hashes PASS; zero observed active conflicts.')
print('All six permutations, five timings per process. Median process-average GFLOPS; screening only. Baseline is local 8629457 / 1d3f5071, not published v55.')
print('\n| Memory | KH | Baseline | Global cutoff | Local check first | Cutoff/base | Local/base |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b,c=[median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | '+ ' | '.join(f'{100*(x/a-1):+.2f}%' for x in [b,c])+' |')
