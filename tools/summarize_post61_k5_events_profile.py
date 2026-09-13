#!/usr/bin/env python3
"""Check K5 output-event ordering attribution and per-thread work conservation."""
from pathlib import Path
from statistics import mean,median
from collections import defaultdict
import re,sys
s=Path(sys.argv[1]).read_text();assert 'K5_EVENTS_DONE' in s and 'FAIL' not in s
for name in ['sources.sha256','profile_sources.sha256']:
    for line in (Path('results/post61/k5-events')/name).read_text().splitlines():
        digest,path=line.split();assert re.search(r'^'+digest+r'\s+'+re.escape(path)+r'$',s,re.M)
m=re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$',s,re.M);assert m
memories=['DDR'] if int(m[1])<0 else ['DDR','HBM'];variants=['baseline','clearfirst','deferclear']
shapes={41:(6144,4096,41,41)}
buckets={41:[0,3],55:[0,1,3],81:[0,2]}
hosts={};threads={};costs={};tables={};counts=defaultdict(int);orders=defaultdict(list);key=None
for line in s.split('K5_EVENTS_SCREEN_DONE')[1].splitlines():
    m=re.match(r'K5_EVENTS_PROFILE memory=(\w+) round=(\d+) variant=(\w+) shape=(\d+) (\d+) (\d+) (\d+)$',line)
    if m:
        kh=int(m[6]);assert tuple(map(int,m.groups()[3:]))==shapes[kh]
        key=m[1],int(m[2]),kh,m[3];orders[key[:3]].append(m[3])
    for prefix,dest in [('K5_PHASE ',hosts),('K5_THREAD ',threads),('K5_COST ',costs),('TABLE_WORK ',tables)]:
        if line.startswith(prefix):
            assert key is not None;fields=dict(re.findall(r'(\w+)=([\d.]+)',line))
            call=int(fields.pop('call'));k=key+(call,)
            if prefix=='K5_THREAD ':k+=(int(fields.pop('tid')),)
            if prefix=='K5_COST ':k+=(int(fields.pop('bucket')),)
            assert k not in dest;dest[k]={n:float(v) for n,v in fields.items()}
    if re.search(r' run\d+\s+.* GFLOPS PASS$',line):
        assert key is not None;counts[key]+=1
blocks={(m,r,k,v) for m in memories for r in range(6) for k in shapes for v in variants}
assert set(counts)==blocks and set(counts.values())=={5}
calls={k+(c,) for k in blocks for c in range(1,8)}
assert set(hosts)==set(tables)==calls
assert set(threads)=={k+(t,) for k in calls for t in range(38)}
assert set(costs)=={k+(b,) for k in calls for b in buckets[k[2]]}
for m in memories:
    for r in range(6):
        for kh in shapes:assert orders[m,r,kh]==[['baseline','clearfirst','deferclear'],['clearfirst','deferclear','baseline'],['deferclear','baseline','clearfirst'],['deferclear','clearfirst','baseline'],['baseline','deferclear','clearfirst'],['clearfirst','baseline','deferclear']][r]
for kh in shapes:
    work=set();storage=set()
    for k in calls:
        if k[2]!=kh:continue
        ts=[threads[k+(t,)] for t in range(38)];cs=[costs[k+(b,)] for b in buckets[kh]]
        work.add(tuple(c['tile_steps'] for c in cs));storage.add(tuple(sorted(tables[k].items())))
        assert sum(t['main_steps']+t['tail_steps'] for t in ts)==sum(c['tile_steps'] for c in cs)
        assert abs(mean(t['main_us'] for t in ts)-costs[k+(0,)]['kernel_mean_us'])<0.002
        assert abs(mean(t['tail_us'] for t in ts)-sum(costs[k+(b,)]['kernel_mean_us'] for b in buckets[kh] if b))<0.004
        assert all(t['main_us']+t['tail_us']<=t['duration_us']+0.003 for t in ts)
    assert len(work)==len(storage)==1
print(f'{len(blocks)} processes, {len(threads)} worker records and {sum(counts.values())} timed hashes validate; work/table totals invariant across all variants per shape.')
print('Six complete permutations, five timings/process; timed calls 3–7, median of process medians. Instrumentation changes code and is attribution only.')
print('\n| Memory | KH | Variant | Prepare us | Pair region us/thread | Other regions us/thread | Last end us | Last-minus-mean end us |')
print('| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |')
for memory in memories:
    for kh in shapes:
        for v in variants:
            procs=defaultdict(list)
            for r in range(6):
                samples=defaultdict(list)
                for c in range(3,8):
                    k=memory,r,kh,v,c;ts=[threads[k+(t,)] for t in range(38)]
                    samples['prepare'].append(hosts[k]['prepare_us'])
                    samples['pair'].append(costs[k+(0,)]['kernel_mean_us'])
                    samples['other'].append(sum(costs[k+(b,)]['kernel_mean_us'] for b in buckets[kh] if b))
                    last=max(t['end_us'] for t in ts)
                    samples['last'].append(last);samples['gap'].append(last-mean(t['end_us'] for t in ts))
                for n,values in samples.items():procs[n].append(median(values))
            print(f'| {memory} | {kh} | {v} | '+' | '.join(f'{median(procs[n]):.3f}' for n in ['prepare','pair','other','last','gap'])+' |')
print('\nRegions include argument setup and ZA restore, not arithmetic-only timings. Per-worker means are not serialized stages; counters cannot identify a physical issue-port cause.')
