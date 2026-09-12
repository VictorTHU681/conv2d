#!/usr/bin/env python3
"""Summarize official per-process averages from alternating validation rounds."""
from collections import defaultdict
from pathlib import Path
import re
from statistics import median
import sys

data = defaultdict(list)
key = None
for line in Path(sys.argv[1]).read_text().splitlines():
    m = re.match(r'OFFICIAL memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+)', line)
    if m:
        key = m[1], m[3], int(m[4])
    m = re.match(r'\s*\d+\s*x\s*\d+\s+\d+\s*x\s*\d+\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)', line)
    if m and key:
        assert m[4] == 'PASS' and float(m[3]) <= 1e-5, line
        data[key].append(float(m[2]))
for mem in ('DDR', 'HBM'):
    print(mem)
    for kh in (39, 41, 55, 81):
        base, cand = data[mem, 'baseline', kh], data[mem, 'candidate', kh]
        if base and cand:
            b, c = median(base), median(cand)
            print(f'k{kh}: {b:.1f} -> {c:.1f} GFLOPS ({100*(c/b-1):+.2f}%), processes={len(base)}/{len(cand)}')
