#!/usr/bin/env python3
"""Compare medians of per-process medians, separately for each memory placement."""
import argparse
from collections import defaultdict
from pathlib import Path
import re
from statistics import median

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('log', type=Path)
args = p.parse_args()
data = defaultdict(list)
key = None
for line in args.log.read_text().splitlines():
    m = re.match(r'MEASURE memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+)', line)
    if m:
        key = (m[1], m[3], int(m[4]), int(m[2]))
    elif line.startswith(('PHASE', 'PROFILE', 'PACK_CONTROL')):
        key = None
    m = re.search(r'run\d+\s+[\d.]+ ms\s+([\d.]+) GFLOPS (\S+)', line)
    if m and key:
        assert m[2] == 'PASS', line
        data[key].append(float(m[1]))
groups = defaultdict(list)
for (mem, v, k, r), values in data.items():
    groups[mem, v, k].append(median(values))
for mem in dict.fromkeys(key[0] for key in data):
    print(mem)
    print('| Variant | k39 | k41 | k55 | k81 |')
    print('|---|---:|---:|---:|---:|')
    for v in dict.fromkeys(key[1] for key in data if key[0] == mem):
        row = [v]
        for k in (39, 41, 55, 81):
            a = groups[mem, v, k]
            base = groups[mem, 'baseline', k]
            row.append(f'{median(a):.1f} ({100*(median(a)/median(base)-1):+.2f}%, n={len(a)})' if a and base else 'pending')
        print('| ' + ' | '.join(row) + ' |')
