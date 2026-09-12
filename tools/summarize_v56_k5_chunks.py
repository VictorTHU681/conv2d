#!/usr/bin/env python3
"""Require complete same-executable continuation-chunk measurements."""
from pathlib import Path
from statistics import median
from collections import defaultdict,Counter
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'K5_CHUNKS_DONE' in s and 'FAIL' not in s
assert re.findall(r'^CHUNK_OWNERSHIP step=(\d+)$',s,re.M)==['2','4','8','16']
assert len(re.findall(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s))==4
steps=[2,4,8,16];data={};counts=defaultdict(int);order=defaultdict(list);key=None
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
for line in s.splitlines():
    m=re.match(r'CHUNK memory=(\w+) round=(\d+) step=(\d+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        assert key is None
        kh=int(m[6]);assert (int(m[4]),int(m[5]),int(m[7]))=={39:(4096,6144,39),41:(6144,4096,41),55:(4256,6390,55),81:(6390,4256,81)}[kh]
        key=m[1],int(m[2]),int(m[3]),kh;order[key[0],key[1],key[3]].append(key[2])
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
    m=re.search(r'\| avg\s+[\d.]+ ms\s+([\d.]+) GFLOPS\s+PASS',line)
    if m:
        assert key is not None and key not in data and counts[key]==5
        data[key]=float(m[1]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in memories for r in range(4) for v in steps for k in [39,41,55,81]}
for m in memories:
    for k in [39,41,55,81]:
        rows=[order[m,r,k] for r in range(4)]
        assert all(set(row)==set(steps) for row in rows)
        assert all({row[p] for row in rows}==set(steps) for p in range(4))
        assert Counter((row[p],row[p+1]) for row in rows for p in range(3))==Counter({(a,b):1 for a in steps for b in steps if a!=b})
print(f'216 signed bitwise output-ownership cases and {len(data)*5} timed output hashes PASS; zero observed active conflicts.')
print('Same binary, four Williams-design rounds, five timings per process. Median process-average GFLOPS; screening only.')
print('\n| Memory | KH | Step 8 default | Step 2 | Step 4 | Step 16 | Step 2/8 | Step 4/8 | Step 16/8 |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b,c,d=[median(data[m,r,v,k] for r in range(4)) for v in [8,2,4,16]]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {d:.1f} | {100*(b/a-1):+.2f}% | {100*(c/a-1):+.2f}% | {100*(d/a-1):+.2f}% |')
