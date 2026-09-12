#!/usr/bin/env python3
"""Strictly validate per-worker continuation phase attribution."""
from pathlib import Path
from collections import defaultdict
from statistics import median,mean
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
assert 'CHUNK_OVERHEAD_DONE' in s and 'FAIL' not in s
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
variants=['s8','s2','s4'];data={};threads={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    m=re.match(r'PROFILE memory=(\w+) round=(\d+) variant=(\w+) shape=6144 4096 41 41$',line)
    if m:key=m[1],int(m[2]),m[3];orders[key[:2]].append(key[2])
    for prefix,dest in [('CHUNK_DETAIL ',data),('K5_THREAD ',threads)]:
        if line.startswith(prefix):
            assert key is not None
            f=dict(re.findall(r'(\w+)=([\d.]+)',line));c=int(f.pop('call'));t=int(f.pop('tid'));k=key+(c,t)
            assert k not in dest;dest[k]={n:float(v) for n,v in f.items()}
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):assert key is not None;counts[key]+=1
blocks={(m,r,v) for m in memories for r in range(6) for v in variants}
assert set(counts)==blocks and set(counts.values())=={5}
expected={k+(c,t) for k in blocks for c in range(1,8) for t in range(38)}
assert set(data)==expected==set(threads)
for m in memories:assert {tuple(orders[m,r]) for r in range(6)}==set(permutations(variants))
row_totals=set();piece_counts=set()
for k in blocks:
    for c in range(1,8):
        ts=[data[k+(c,t)] for t in range(38)]
        assert sum(t['resumes'] for t in ts)==sum(t['saves'] for t in ts)
        row_totals.add(sum(t['rows'] for t in ts));piece_counts.add(sum(t['chunks']-t['resumes'] for t in ts))
        for tid,t in enumerate(ts):
            assert t['resumes']<=t['chunks'] and t['saves']<=t['chunks'] and t['steals']<=t['chunks']
            # Timers bracket disjoint regions; allow printed rounding error.
            assert sum(t[n] for n in ['claim_us','setup_us','restore_us','kernel_us','publish_us']) <= threads[k+(c,tid)]['duration_us']+0.02
assert len(row_totals)==len(piece_counts)==1
print(f'{len(blocks)} processes, {len(data)} phase records, {sum(counts.values())} timed hashes PASS. Saves equal resumes; every call processes {next(iter(row_totals)):.0f} rows across {next(iter(piece_counts)):.0f} pieces.')
print('Timed calls 3–7: median of six process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.')
print('Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.')
print('\n| Memory | Step | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
metrics=['chunks','steals','claim_us','setup_us','restore_us','kernel_us','publish_us']
for m in memories:
    for v in variants:
        proc=defaultdict(list)
        for r in range(6):
            calls=defaultdict(list)
            for c in range(3,8):
                ts=[data[m,r,v,c,t] for t in range(38)]
                for n in metrics:calls[n].append(mean(t[n] for t in ts))
                calls['last'].append(max(threads[m,r,v,c,t]['end_us'] for t in range(38)))
            for n,a in calls.items():proc[n].append(median(a))
        print(f'| {m} | {v} | '+' | '.join(f'{median(proc[n]):.3f}' for n in metrics+['last'])+' |')
