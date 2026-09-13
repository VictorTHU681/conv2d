#!/usr/bin/env python3
"""Audit PAIRF3 compute suffix unroll candidate using the unchanged original benchmark."""
from pathlib import Path
from collections import defaultdict
from statistics import median
import re
import hashlib
import sys

s = Path(sys.argv[1]).read_text()
assert 'PAIRF3_UNROLL_REPEAT_DONE' in s and 'FAIL' not in s
for line in Path('results/post64/pairf3-unroll/sources.sha256').read_text().splitlines():
    digest, path = line.split()
    if Path(path).name not in ['baseline.c','u4.c','bench_conv.c']: continue
    assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$', s, re.M)
assert 'STATE_SWEEP' not in s
variants = ['baseline', 'u4']
for v in variants:
    assert re.search(r'^[0-9a-f]{64}\s+build/post64/pairf3-unroll/official_'+v+r'$', s, re.M)
binaries=['official_baseline','official_u4']
for name in binaries:
    path=Path('build/post64/pairf3-unroll')/name
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert re.search(r'^'+digest+r'\s+'+re.escape(str(path))+r'$',s,re.M), name
print('Both downloaded binaries match their pre-execution SHA-256 records.')
m = re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$', s, re.M)
assert m
memories = ['DDR'] if int(m[1]) < 0 else ['DDR', 'HBM']
shapes = {39:(4096,6144,39,39), 41:(6144,4096,41,41),
          55:(4256,6390,55,55), 81:(6390,4256,81,81)}
data = {}
orders = defaultdict(list)
key = None
for line in s.splitlines():
    m = re.match(r'PAIRF3_UNROLL_REPEAT memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$', line)
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
print('Fixed binaries from job 1592972, repeated on a separate node without recompiling; no runtime layout knob. Six alternating orders, five timings/process; median process-average GFLOPS. Baseline is current upstream b6ea996/138dcac source 08400a76. These ratios compare PAIRF3 compute suffix unrolls directly to that baseline; no gains are added from earlier experiments.')
print('\n| Memory | KH | Upstream | U4 | U4/upstream |')
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
