#!/usr/bin/env python3
"""Validate the six-permutation original-benchmark experiment."""
from pathlib import Path
from collections import defaultdict,Counter
from statistics import median
from itertools import permutations
import re,sys
data={};order=defaultdict(list)
for filename in sys.argv[1:]:
    s=Path(filename).read_text();assert 'K33_UNROLL_OFFICIAL_DONE' in s and 'FAIL' not in s
    key=None
    for line in s.splitlines():
        m=re.match(r'OFFICIAL memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+) (\d+)',line)
        if m:
            assert key is None and m[4]==m[5]
            key=m[1],int(m[2]),m[3],int(m[4])
            order[key[0],key[1],key[3]].append(key[2])
        m=re.match(r'\s*\d+\s*x\s*\d+\s+\d+\s*x\s*\d+\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
        if m and key:
            assert m[4]=='PASS' and float(m[3])==0 and key not in data
            data[key]=float(m[2]);key=None
    assert key is None
variants=['baseline','outline','unroll4']
expected={(m,r,v,k) for m in ['DDR','HBM'] for r in range(6) for v in variants for k in [39,41,55,81]}
assert set(data)==expected
for mem in ['DDR','HBM']:
    for k in [39,41,55,81]:
        assert {tuple(order[mem,r,k]) for r in range(6)}==set(permutations(variants))
print('All 144 complete-reference checks PASS, maximum errors zero. All six process permutations occur once per shape/memory.')
print('Each value is the median of six process-average GFLOPS values, five timed calls per process.')
print('\n| Memory | KH=KW | Baseline | Outline | Unroll4 | Outline vs baseline | Unroll4 vs baseline | Unroll4 vs outline |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for mem in ['DDR','HBM']:
    for k in [39,41,55,81]:
        a,b,c=[median(data[mem,r,v,k] for r in range(6)) for v in variants]
        print(f'| {mem} | {k} | {a:.1f} | {b:.1f} | {c:.1f} | {100*(b/a-1):+.2f}% | {100*(c/a-1):+.2f}% | {100*(c/b-1):+.2f}% |')
