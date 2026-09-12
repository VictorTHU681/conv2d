#!/usr/bin/env python3
"""Require complete acceptance records before reporting paired performance."""
from pathlib import Path
from statistics import median
import re,sys

s=Path(sys.argv[1]).read_text()
pipeline='OUTPUT_PIPELINE_DONE' in s
candidate='pipelined' if pipeline else 'ordered'
assert ('OUTPUT_PIPELINE_DONE' if pipeline else 'OUTPUT_ORDER_DONE') in s and 'FAIL' not in s
if pipeline:
    assert re.search(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s)
assert s.count('STATE_SWEEP PASS cases=261')==5
assert s.count('PLANAR_GUARD_PASS cases=224')==1
data={};order={};key=None
for line in s.splitlines():
    m=re.match(r'OFFICIAL memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+) (\d+)',line)
    if m:
        assert key is None and m[4]==m[5]
        key=m[1],int(m[2]),m[3],int(m[4])
        order.setdefault((key[0],key[1],key[3]),[]).append(key[2])
    m=re.match(r'\s*\d+\s*x\s*\d+\s+\d+\s*x\s*\d+\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m and key:
        assert key not in data and m[4]=='PASS' and float(m[3])==0
        data[key]=float(m[2]);key=None
assert key is None
assert set(data)=={(m,r,v,k) for m in ['DDR','HBM'] for r in range(4)
                   for v in ['baseline',candidate] for k in [39,41,55,81]}
for (m,r,k),v in order.items():
    assert v==(['baseline',candidate] if r%2==0 else [candidate,'baseline'])
print('1,305 state cases, 224 guard cases, 64 official full-reference checks PASS; official maximum errors zero.')
print('Four rounds alternate process order. Five timings per process; median of four process-average GFLOPS.')
if pipeline: print('Additional 54 signed bitwise runtime overlap-audit cases PASS, zero observed active conflicts.')
print(f'\n| Memory | KH=KW | Baseline GFLOPS | {candidate.title()} GFLOPS | Change |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in ['DDR','HBM']:
    for k in [39,41,55,81]:
        a,b=[median(data[m,r,v,k] for r in range(4)) for v in ['baseline',candidate]]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {100*(b/a-1):+.2f}% |')
