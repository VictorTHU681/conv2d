#!/usr/bin/env python3
"""Summarize per-run GFLOPS from a v51 same-node screening log."""
import argparse
from collections import defaultdict
from pathlib import Path
import re
import statistics

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('log', type=Path)
parser.add_argument('--official', action='store_true', help='Summarize alternating official-reference acceptance runs')
args = parser.parse_args()
data = defaultdict(list)
key = None
for line in args.log.read_text().splitlines():
    if args.official:
        if line.startswith('PLAIN_ACCEPT'):
            key = None
        m = re.match(r'OFFICIAL_ACCEPT round=(\d+) variant=(\S+) shape=(.*)', line)
        if m:
            key = (m[2], int(m[3].split()[2]))
        m = re.match(r'\s*\d+ x\s*\d+\s+\d+ x\s*\d+\s+[\d.]+\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)', line)
        if m and key:
            if m[3] != 'PASS':
                raise SystemExit('An official output failed validation: ' + line)
            data[key].append(float(m[1]))
            key = None
        continue
    if line.startswith(('OFFICIAL_BASELINE', 'BASELINE_LOCAL_DDR',
                        'BASELINE_KERNEL_PROFILE', 'MEMORY_AND_KERNEL')):
        key = None
    m = re.match(r'MEASURE round=(\d+) variant=(\S+) shape=(.*)', line)
    if m:
        key = (m[2], int(m[3].split()[2]))
    m = re.search(r'run\d+\s+([\d.]+) ms\s+([\d.]+) GFLOPS (\S+)', line)
    if m and key:
        if m[3] != 'PASS':
            raise SystemExit('A timed output failed validation: ' + line)
        data[key].append(float(m[2]))
variants = list(dict.fromkeys(v for v, _ in data))
print('| Variant | k39 | k41 | k55 | k81 |')
print('|---|---:|---:|---:|---:|')
for v in variants:
    cells = []
    for k in (39, 41, 55, 81):
        if (v, k) not in data:
            cells.append('pending')
            continue
        median = statistics.median(data[v, k])
        base = statistics.median(data['baseline', k])
        cells.append(f'{median:.1f} ({100*(median/base-1):+.2f}%, n={len(data[v,k])})')
    print('| ' + ' | '.join([v] + cells) + ' |')
