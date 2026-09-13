#!/usr/bin/env python3
"""Require all 72 official checks and summarize corrected v56 against both baselines."""
from collections import defaultdict
from pathlib import Path
import re
from statistics import median
import sys
logs=[Path(p).read_text() for p in sys.argv[1:]]
assert logs and all("OFFICIAL_DONE" in s for s in logs), "incomplete input job"
log="\n".join(logs)
data=defaultdict(list); key=None
for line in log.splitlines():
    m=re.match(r'OFFICIAL memory=(\w+) round=(\d+) variant=(\w+) shape=\d+ \d+ (\d+)',line)
    if m: key=(m[1],m[3],int(m[4]))
    m=re.match(r'\s*\d+\s*x\s*\d+\s+\d+\s*x\s*\d+\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)',line)
    if m and key:
        assert m[4]=='PASS' and float(m[3])==0,line
        data[key].append(float(m[2]))
assert 'OFFICIAL_DONE' in log,'official job has not completed'
assert sum(map(len,data.values()))==72
print('| Memory | Kernel | v55 GFLOPS | Previous v56 | Corrected v56 | vs v55 | vs previous v56 |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: |')
for memory in ('DDR','HBM'):
    for kh in (39,41,55,81):
        vals=[]
        for variant in ('baseline','previous','candidate'):
            runs=data[memory,variant,kh];assert len(runs)==3,(memory,variant,kh)
            vals.append(median(runs))
        b,p,c=vals
        print(f'| {memory} | {kh} | {b:.1f} | {p:.1f} | {c:.1f} | {100*(c/b-1):+.2f}% | {100*(c/p-1):+.2f}% |')
