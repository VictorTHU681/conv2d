#!/usr/bin/env python3
"""Strictly validate per-worker continuation phase attribution."""
from pathlib import Path
from collections import defaultdict,Counter
from statistics import median,mean
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text()
setup55='CHUNK_SETUP55_PROFILE_DONE' in s
setup=setup55 or 'CHUNK_SETUP_PROFILE_DONE' in s
assert ('CHUNK_SETUP55_PROFILE_DONE' if setup55 else 'CHUNK_SETUP_PROFILE_DONE' if setup else 'CHUNK_OVERHEAD_DONE') in s and 'FAIL' not in s
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM']
variants=['baseline','phase','carry4','both'] if setup else ['s8','s2','s4']
rounds=range(4 if setup else 6)
data={};threads={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.splitlines():
    shape='4256 6390 55 55' if setup55 else '6144 4096 41 41'
    m=re.match(r'PROFILE memory=(\w+) round=(\d+) variant=(\w+) shape='+shape+'$',line)
    if m:key=m[1],int(m[2]),m[3];orders[key[:2]].append(key[2])
    for prefix,dest in [('CHUNK_DETAIL ',data),('K5_THREAD ',threads)]:
        if line.startswith(prefix):
            assert key is not None
            f=dict(re.findall(r'(\w+)=([\d.]+)',line));c=int(f.pop('call'));t=int(f.pop('tid'));k=key+(c,t)
            assert k not in dest;dest[k]={n:float(v) for n,v in f.items()}
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):assert key is not None;counts[key]+=1
blocks={(m,r,v) for m in memories for r in rounds for v in variants}
assert set(counts)==blocks and set(counts.values())=={5}
expected={k+(c,t) for k in blocks for c in range(1,8) for t in range(38)}
assert set(data)==expected==set(threads)
for m in memories:
    rows=[orders[m,r] for r in rounds]
    if setup:
        assert all(set(row)==set(variants) for row in rows)
        assert all({row[p] for row in rows}==set(variants) for p in range(4))
        assert Counter((row[p],row[p+1]) for row in rows for p in range(3))==Counter({(a,b):1 for a in variants for b in variants if a!=b})
    else:assert {tuple(row) for row in rows}==set(permutations(variants))
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
print('Timed calls 3–7: median of '+('four' if setup else 'six')+' process medians of per-call worker means. Extra counter reads perturb execution; timings include boundary instrumentation and are attribution only.')
print('Restore includes first-chunk ZA zeroing. Publish includes existing diagnostic accounting, ZA save and release. Setup excludes kernel-internal ring initialization; kernel includes that initialization and vector carry.')
print('\n| Memory | '+('Variant' if setup else 'Step')+' | Chunks/thread | Steals/thread | Claim us | Setup us | ZA restore/zero us | Kernel us | Save/publish us | Last end us |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
metrics=['chunks','steals','claim_us','setup_us','restore_us','kernel_us','publish_us']
for m in memories:
    for v in variants:
        proc=defaultdict(list)
        for r in rounds:
            calls=defaultdict(list)
            for c in range(3,8):
                ts=[data[m,r,v,c,t] for t in range(38)]
                for n in metrics:calls[n].append(mean(t[n] for t in ts))
                calls['last'].append(max(threads[m,r,v,c,t]['end_us'] for t in range(38)))
                for n in ['main_us','tail_us']:
                    calls[n].append(mean(threads[m,r,v,c,t][n] for t in range(38)))
            for n,a in calls.items():proc[n].append(median(a))
        print(f'| {m} | {v} | '+' | '.join(f'{median(proc[n]):.3f}' for n in metrics+['last'])+' |')

if setup55:
    print('\nKH55 kernel-region detail uses the existing diagnostic buckets (setup + restore + kernel, not arithmetic-only).')
    print('\n| Memory | Variant | Main F3 region us/thread | Tail single-16 region us/thread |')
    print('| --- | --- | ---: | ---: |')
    for m in memories:
        for v in variants:
            vals={n:[] for n in ['main_us','tail_us']}
            for r in rounds:
                for n in vals:vals[n].append(median(mean(threads[m,r,v,c,t][n] for t in range(38)) for c in range(3,8)))
            print(f'| {m} | {v} | {median(vals["main_us"]):.3f} | {median(vals["tail_us"]):.3f} |')
