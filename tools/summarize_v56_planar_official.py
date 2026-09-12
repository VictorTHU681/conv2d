#!/usr/bin/env python3
"""Strictly validate and summarize the complete three-way official comparison."""
from collections import defaultdict
from pathlib import Path
from statistics import median
import re
import sys

s=Path(sys.argv[1]).read_text()
assert 'PLANAR_OFFICIAL_DONE' in s and 'FAIL' not in s
data={};key=None
for line in s.splitlines():
    m=re.match(r'OFFICIAL memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+) (\d+)',line)
    if m:
        assert key is None and m[4]==m[5]
        key=(m[1],int(m[2]),m[3],int(m[4]))
        continue
    m=re.match(r'\s*\d+\s*x\s*\d+\s+\d+\s*x\s*\d+\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m and key:
        assert m[4]=='PASS' and float(m[3])==0 and key not in data
        data[key]=float(m[2]);key=None
assert key is None
memories=list(dict.fromkeys(k[0] for k in data))
assert set(memories)<= {'DDR','HBM'} and 'DDR' in memories
expected={(mem,r,v,k) for mem in memories for r in (1,2,3) for v in ('baseline','upstream','mergedfixed') for k in (39,41,55,81)}
assert set(data)==expected
print(f'{len(data)} complete-reference checks PASS, all maximum errors 0.')
print('Each cell uses the median of three process-average GFLOPS values (five timed calls per process).')
print('\n| Memory | KH=KW | Local baseline | Upstream | Integrated | vs local | vs upstream |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for mem in memories:
    for k in (39,41,55,81):
        a,b,c=[median(data[mem,r,v,k] for r in (1,2,3)) for v in ('baseline','upstream','mergedfixed')]
        print(f'| {mem} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {100*(c/a-1):+.2f}% | {100*(c/b-1):+.2f}% |')
