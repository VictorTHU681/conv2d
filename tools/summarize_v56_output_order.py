#!/usr/bin/env python3
"""Require complete acceptance records before reporting paired performance."""
from pathlib import Path
from statistics import median
import re,sys

s=Path(sys.argv[1]).read_text()
pipeline='OUTPUT_PIPELINE_DONE' in s
shared='KF_SHARE_DONE' in s
upstream='UPSTREAM_GATE_DONE' in s or shared
candidate='merged' if upstream else 'pipelined' if pipeline else 'ordered'
assert ('KF_SHARE_DONE' if shared else 'UPSTREAM_GATE_DONE' if upstream else 'OUTPUT_PIPELINE_DONE' if pipeline else 'OUTPUT_ORDER_DONE') in s and 'FAIL' not in s
if shared:
    assert 'KF_SHARE_PASS cases=288 shared_groups=144 nonowner_rows=23184 values=26023296 gate_checks=2' in s
    assert 'KF_GATE_POSITIVE detected_missing_dependency=1' in s
if pipeline or upstream:
    assert re.search(r'OUTPUT_OVERLAP PASS cases=54 calls=\d+ active_conflicts=0 positive_control=0',s)
assert s.count('STATE_SWEEP PASS cases=261')==5
guards=272 if upstream else 224
assert s.count(f'PLANAR_GUARD_PASS cases={guards}')==1
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
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M)
assert placement is not None
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
assert set(data)=={(m,r,v,k) for m in memories for r in range(4)
                   for v in ['baseline',candidate] for k in [39,41,55,81]}
for (m,r,k),v in order.items():
    assert v==(['baseline',candidate] if r%2==0 else [candidate,'baseline'])
print(f'1,305 state cases, {guards} guard cases, {len(data)} official full-reference checks PASS; official maximum errors zero.')
if shared: print('Additional 288 table ownership/content cases and the missing-dependency positive control PASS.')
print('Four rounds alternate process order. Five timings per process; median of four process-average GFLOPS.')
if pipeline or upstream: print('Additional 54 signed bitwise runtime overlap-audit cases PASS, zero observed active conflicts.')
if len(memories)==1: print('HBM unavailable in this allocation; no HBM result is claimed.')
print(f'\n| Memory | KH=KW | Baseline GFLOPS | {candidate.title()} GFLOPS | Change |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in [39,41,55,81]:
        a,b=[median(data[m,r,v,k] for r in range(4)) for v in ['baseline',candidate]]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {100*(b/a-1):+.2f}% |')
