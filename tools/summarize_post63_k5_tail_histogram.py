#!/usr/bin/env python3
"""Audit observed K5 tail geometry independently of timing candidates."""
from pathlib import Path
from collections import defaultdict
import re,sys

s=Path(sys.argv[1]).read_text()
assert 'K5_TAIL_DONE' in s and 'FAIL' not in s
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
assert re.search(r'^[0-9a-f]{64}\s+build/post63/k5-tail/histogram$',s,re.M)
for line in Path('results/post63/k5-tail/sources.sha256').read_text().splitlines():
    h,p=line.split()
    if p.endswith('/histogram.c'):assert re.search(r'^'+h+r'\s+'+re.escape(p)+r'$',s,re.M)
work={int(m[1]) for m in re.finditer(r'^K5_COST call=\d+ bucket=3 tile_steps=(\d+) ',s,re.M)}
assert len(work)==1
expected_rows=next(iter(work))//(4*43)
assert expected_rows*4*43==next(iter(work))
data={};counts=defaultdict(int);avgs=[];memory=None
for line in s.split('K5_TAIL_HISTOGRAM_BEGIN')[1].splitlines():
    m=re.fullmatch(r'K5_TAIL_GEOMETRY memory=(\w+) shape=6144 4096 41 41',line)
    if m:
        memory=m[1];assert memory in memories
    m=re.fullmatch(r'K5_TAIL_HIST call=(\d+) triples=(\d+) scalars=(\d+) calls=(\d+) rows=(\d+)',line)
    if m:
        assert memory is not None
        call,t,r,calls,rows=map(int,m.groups())
        assert 1<=call<=7 and 0<=t<16 and 0<=r<3 and rows>=calls>0
        key=memory,call,t,r
        assert key not in data;data[key]=(calls,rows)
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):counts[memory]+=1
    if re.search(r'\| avg\s+[\d.]+ ms\s+[\d.]+ GFLOPS\s+PASS',line):avgs.append(memory)
assert set(counts)==set(memories) and set(counts.values())=={5} and avgs==memories
assert {(k[0],k[1]) for k in data}=={(m,c) for m in memories for c in range(1,8)}
for m in memories:
    for c in range(1,8):
        assert sum(v[1] for k,v in data.items() if k[:2]==(m,c))==expected_rows
print(f'{len(memories)*7} complete diagnostic calls and {sum(counts.values())} timed hashes PASS. Each call totals {expected_rows} K5 rows, matching independently profiled tile work.')
print('Counts are from a separate instrumented executable. They describe observed geometry, not the allocation alignment of every uninstrumented timing process; diagnostic timings are not used for acceptance.')
print('\n| Memory | Tail triples | Scalars | Calls summed | Rows summed | Row share |')
print('| --- | ---: | ---: | ---: | ---: | ---: |')
for m in memories:
    groups=defaultdict(lambda:[0,0])
    for k,(calls,rows) in data.items():
        if k[0]==m:
            groups[k[2:]][0]+=calls;groups[k[2:]][1]+=rows
    total=sum(v[1] for v in groups.values())
    for (t,r),(calls,rows) in sorted(groups.items()):
        print(f'| {m} | {t} | {r} | {calls} | {rows} | {100*rows/total:.2f}% |')
    empty=sum(v[1] for k,v in groups.items() if k[0]==0)
    print(f'\n{m}: empty vector tail {100*empty/total:.2f}% of observed K5 rows.\n')
