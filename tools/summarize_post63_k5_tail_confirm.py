#!/usr/bin/env python3
"""Audit fixed scalar-tail candidates using the unchanged original benchmark."""
from pathlib import Path
from collections import defaultdict
from itertools import permutations
from statistics import median
import re
import sys

s = Path(sys.argv[1]).read_text()
assert 'K5_TAIL_CONFIRM_DONE' in s and 'FAIL' not in s
for line in Path('results/post63/k5-tail/official_sources.sha256').read_text().splitlines():
    digest, path = line.split()
    if Path(path).name not in ['baseline.c','unroll.c','bench_conv.c']: continue
    assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$', s, re.M)
variants = ['baseline', 'unroll']
for v in variants:
    assert re.search(r'^[0-9a-f]{64}\s+build/post63/k5-tail/official_'+v+r'$', s, re.M)
m = re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$', s, re.M)
assert m
memories = ['DDR'] if int(m[1]) < 0 else ['DDR', 'HBM']
shapes = {39:(4096,6144,39,39), 41:(6144,4096,41,41),
          55:(4256,6390,55,55), 81:(6390,4256,81,81)}
data = {}
orders = defaultdict(list)
key = None
for line in s.splitlines():
    m = re.match(r'K5_TAIL_CONFIRM memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$', line)
    if m:
        assert key is None
        kh = int(m[6])
        assert tuple(map(int, m.groups()[3:])) == shapes[kh]
        key = m[1], int(m[2]), m[3], kh
        orders[key[0],key[1],kh].append(key[2])
    m = re.match(r'\s*(\d+)\s*x\s*(\d+)\s+(\d+)\s*x\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)', line)
    if m:
        assert key is not None and key not in data
        assert tuple(map(int,m.groups()[:4])) == shapes[key[3]]
        assert m[8] == 'PASS' and float(m[7]) == 0
        data[key] = float(m[6])
        key = None
assert key is None
assert set(data) == {(m,r,v,k) for m in memories for r in range(6) for v in variants for k in shapes}
for m in memories:
    for k in shapes:
        assert [orders[m,r,k] for r in range(6)] == [variants if r%2==0 else variants[::-1] for r in range(6)]
print(f'{len(data)} original full-reference checks PASS; maximum errors zero.')
print('Independent fixed sources, no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is unchanged published v62/v63 cf42580/5a423250. These ratios compare the scalar-tail-unrolled candidate directly to the current production kernel; no gains are added from earlier v62/v63 experiments.')
print('\n| Memory | KH | v62/v63 | Unroll | Unroll/v62/v63 |')
print('| --- | ---: | ---: | ---: | ---: |')
for m in memories:
    for k in shapes:
        a,b = [median(data[m,r,v,k] for r in range(6)) for v in variants]
        print(f'| {m} | {k} | {a:.1f} | {b:.1f} | {100*(b/a-1):+.2f}% |')
print('\nAll paired outliers retained; observed ranges are not confidence intervals.')
for m in memories:
    for k in shapes:
        for v in variants[1:]:
            xs = [100*(data[m,r,v,k]/data[m,r,'baseline',k]-1) for r in range(6)]
            print(f'{m} KH{k} {v}: paired median {median(xs):+.2f}%, range {min(xs):+.2f}..{max(xs):+.2f}%, positive {sum(x>0 for x in xs)}/6')
