#!/usr/bin/env python3
"""Summarize timed diagnostic calls separately from uninstrumented sampling overhead."""
from pathlib import Path
from collections import defaultdict
from statistics import median
import re
root=Path('results/v56/experiments/k41-profile')
s=(root/'lowrate.log').read_text();assert 'V56_K41_SAMPLE_DONE' in s
phase=defaultdict(list);copies=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'PHASE memory=(\w+) round=(\d+) variant=(\w+)',line)
    if m:key=m[1],m[3],int(m[2])
    if line.startswith(('UNSAMPLED','LOW_RATE')):key=None
    if key and line.startswith(('[v56-phase]','[first-copy-cost]')):
        row={a:float(b) for a,b in re.findall(r'(\w+)=([\d.]+)',line)}
        (phase if line.startswith('[v56-phase]') else copies)[key].append(row)
print('| Memory | Variant | Prepare us | Host pack us | Workers us | Mean first copy us/thread | First copy % |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: |')
for memory in ['DDR','HBM']:
    for variant in ['previous','baseline']:
        keys=[(memory,variant,r) for r in [1,2,3]]
        assert all(len(phase[k])==7 and len(copies[k])==7 for k in keys)
        ps=[x for k in keys for x in phase[k][2:]];cs=[x for k in keys for x in copies[k][2:]]
        vals=[median(x[n] for x in ps) for n in ['prepare_us','host_pack_us','workers_us']]
        vals += [median(x[n] for x in cs) for n in ['mean_copy_us','copy_pct']]
        print(f'| {memory} | {variant} | '+' | '.join(f'{x:.4f}' for x in vals)+' |')
print('\nSampling overhead control (steady allocation; not official timings):')
steady={}
for tag,memory,v,ms in re.findall(r'(UNSAMPLED|LOW_RATE_SAMPLE) memory=(\w+) variant=(\w+)[^\n]*\nSTEADY_DIAGNOSTIC[^\n]*mean_ms=([\d.]+)',s):
    steady[memory,v,tag]=float(ms)
for memory in ['DDR','HBM']:
    for v in ['previous','baseline']:
        a,b=[steady[memory,v,t] for t in ['UNSAMPLED','LOW_RATE_SAMPLE']]
        print(f'{memory} {v}: {a:.4f} -> {b:.4f} ms ({100*(b/a-1):+.2f}% with 99-Hz sampling)')
