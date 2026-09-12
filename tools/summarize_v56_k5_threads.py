#!/usr/bin/env python3
"""Validate thread records and characterize the last worker, not printed GFLOPS."""
from pathlib import Path
from collections import defaultdict,Counter
from statistics import median,mean
from itertools import permutations
import re,sys
s=Path(sys.argv[1]).read_text();chunks='K5_CHUNK_THREAD_DONE' in s
assert ('K5_CHUNK_THREAD_DONE' if chunks else 'K5_THREAD_DONE') in s and 'FAIL' not in s
placement=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert placement
memories=['DDR'] if int(placement[1])<0 else ['DDR','HBM']
variants=['s8','s2','s4'] if chunks else ['baseline','triplet','k5cost']
data={};counts=defaultdict(int);order=defaultdict(list);steps=defaultdict(int);key=None
for line in s.splitlines():
    m=re.match(r'PROFILE memory=(\w+) round=(\d+) variant=(\w+) shape=6144 4096 41 41$',line)
    if m:key=m[1],int(m[2]),m[3];order[key[:2]].append(key[2])
    if line.startswith('K5_THREAD '):
        assert key is not None;fields=dict(re.findall(r'(\w+)=([\d.]+)',line))
        call=int(fields.pop('call'));tid=int(fields.pop('tid'));k=key+(call,tid)
        assert k not in data;data[k]={f:float(v) for f,v in fields.items()}
        assert abs(data[k]['end_us']-data[k]['start_us']-data[k]['duration_us'])<0.003
    m=re.match(r'K5_COST call=(\d+) bucket=\d+ tile_steps=(\d+) ',line)
    if m:assert key is not None;steps[key+(int(m[1]),)]+=int(m[2])
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):assert key is not None;counts[key]+=1
blocks={(m,r,v) for m in memories for r in range(6) for v in variants}
assert set(counts)==blocks and set(counts.values())=={5}
assert set(data)=={k+(c,t) for k in blocks for c in range(1,8) for t in range(38)}
assert set(steps)=={k+(c,) for k in blocks for c in range(1,8)}
for k in steps: assert sum(data[k+(t,)]['main_steps']+data[k+(t,)]['tail_steps'] for t in range(38))==steps[k]
for m in memories: assert {tuple(order[m,r]) for r in range(6)}==set(permutations(variants))
print(f'{len(blocks)} processes, {len(data)} thread records and {sum(counts.values())} timed output hashes PASS; thread step sums match aggregate kernel counts.')
print('Timed calls 3–7 only. Median of six process medians. End times are relative to the first worker start in each call.')
print('Detailed printing happens after workers join and perturbs benchmark wall time; these records characterize workers, not production speed.')
print('\n| Memory | Variant | Last end us | End spread us | Last end minus mean us | Last worker start us | Last worker main us | Last worker tail us | Tail-majority last workers | Most frequent last IDs |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
for m in memories:
    for v in variants:
        vals=defaultdict(list);lasts=Counter();tail_major=0
        for r in range(6):
            proc=defaultdict(list)
            for c in range(3,8):
                ts=[data[m,r,v,c,t] for t in range(38)];last=max(range(38),key=lambda t:ts[t]['end_us']);q=ts[last];lasts[last]+=1
                tail_major+=q['tail_us']>q['main_us']
                a=[q['end_us'],q['end_us']-min(x['end_us'] for x in ts),q['end_us']-mean(x['end_us'] for x in ts),q['start_us'],q['main_us'],q['tail_us']]
                for i,x in enumerate(a):proc[i].append(x)
            for i,x in proc.items():vals[i].append(median(x))
        row=[median(vals[i]) for i in range(6)]
        ids=', '.join(f'{t}:{n}' for t,n in lasts.most_common(4))
        print(f'| {m} | {v} | '+' | '.join(f'{x:.3f}' for x in row)+f' | {tail_major}/30 | {ids} |')
